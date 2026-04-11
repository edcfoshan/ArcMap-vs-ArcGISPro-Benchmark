(function () {
  "use strict";

  var state = null;
  var bootstrapped = false;
  var pollTimer = null;

  var els = {
    jobStatus: document.getElementById("job-status"),
    serverSummary: document.getElementById("server-summary"),
    currentScale: document.getElementById("current-scale"),
    currentStage: document.getElementById("current-stage"),
    sessionRoot: document.getElementById("session-root"),
    progressText: document.getElementById("progress-text"),
    progressBar: document.getElementById("progress-bar"),
    substatus: document.getElementById("substatus"),
    logOutput: document.getElementById("log-output"),
    scaleTableBody: document.getElementById("scale-table-body"),
    python27Path: document.getElementById("python27-path"),
    python3Path: document.getElementById("python3-path"),
    outputBaseDir: document.getElementById("output-base-dir"),
    runs: document.getElementById("runs"),
    warmup: document.getElementById("warmup"),
    mpWorkers: document.getElementById("mp-workers"),
    generateData: document.getElementById("generate-data"),
    includeOpensource: document.getElementById("include-opensource"),
    multiprocess: document.getElementById("multiprocess"),
    startButton: document.getElementById("start"),
    stopButton: document.getElementById("stop"),
    refreshButton: document.getElementById("refresh"),
    presetFirstThree: document.getElementById("preset-first-three"),
    presetFast: document.getElementById("preset-fast"),
    scaleList: document.getElementById("scale-list"),
  };

  var stageOrder = ["py2", "py3", "os", "analysis", "validation"];
  var stageLabels = {
    py2: "Py2",
    py3: "Py3",
    os: "开源库",
    analysis: "分析",
    validation: "校验",
  };

  function apiGet(path) {
    return fetch(path, { cache: "no-store" }).then(function (res) {
      if (!res.ok) {
        throw new Error("GET " + path + " 失败，状态码 " + res.status);
      }
      return res.json();
    });
  }

  function apiPost(path, payload) {
    return fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {}),
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) {
          var message = data && data.error ? data.error : ("POST " + path + " 失败，状态码 " + res.status);
          throw new Error(message);
        }
        return data;
      });
    });
  }

  function formatPath(value) {
    return value || "-";
  }

  function statusClass(status) {
    if (status === "completed" || status === "passed") {
      return "badge badge-passed";
    }
    if (status === "stopped") {
      return "badge badge-skipped";
    }
    if (status === "idle") {
      return "badge badge-pending";
    }
    if (status === "error") {
      return "badge badge-failed";
    }
    return "badge badge-" + (status || "pending");
  }

  function badgeLabel(status) {
    if (status === "passed") {
      return "通过";
    }
    if (status === "failed") {
      return "失败";
    }
    if (status === "running") {
      return "运行中";
    }
    if (status === "skipped") {
      return "跳过";
    }
    if (status === "completed") {
      return "完成";
    }
    if (status === "stopped") {
      return "已停止";
    }
    if (status === "idle") {
      return "空闲";
    }
    if (status === "error") {
      return "错误";
    }
    return "等待中";
  }

  function stageLabel(stageName) {
    return stageLabels[stageName] || stageName;
  }

  function stageSummary(stage) {
    if (!stage) {
      return "暂无数据";
    }

    var pieces = [];
    if (stage.return_code !== null && typeof stage.return_code !== "undefined") {
      pieces.push("返回码 " + stage.return_code);
    }
    if (typeof stage.duration_sec === "number") {
      pieces.push(stage.duration_sec.toFixed(1) + " 秒");
    }
    if (stage.details && stage.details.count) {
      pieces.push("结果 " + stage.details.count + " 条");
    }
    if (stage.summary) {
      pieces.push(stage.summary);
    }
    return pieces.join(" | ");
  }

  function scaleRow(scaleState) {
    var tr = document.createElement("tr");

    var scaleCell = document.createElement("td");
    scaleCell.innerHTML = "<strong>" + scaleState.scale + "</strong><div class='badge-sub'>" + badgeLabel(scaleState.status || "pending") + "</div>";
    tr.appendChild(scaleCell);

    var dirCell = document.createElement("td");
    dirCell.innerHTML = "<span class='mono'>" + formatPath(scaleState.output_dir) + "</span>";
    tr.appendChild(dirCell);

    stageOrder.forEach(function (stageName) {
      var stage = scaleState.stages ? scaleState.stages[stageName] : null;
      var td = document.createElement("td");
      var badge = document.createElement("div");
      badge.className = statusClass(stage ? stage.status : "pending");
      badge.textContent = badgeLabel(stage ? stage.status : "pending");
      td.appendChild(badge);

      var sub = document.createElement("div");
      sub.className = "badge-sub";
      sub.textContent = stageSummary(stage);
      td.appendChild(sub);
      tr.appendChild(td);
    });

    return tr;
  }

  function selectedScales() {
    var items = [];
    var inputs = els.scaleList.querySelectorAll("input[type='checkbox']");
    Array.prototype.forEach.call(inputs, function (input) {
      if (input.checked) {
        items.push(input.value);
      }
    });
    return items;
  }

  function setSelectedScales(scales) {
    var wanted = {};
    (scales || []).forEach(function (scale) {
      wanted[String(scale)] = true;
    });
    var inputs = els.scaleList.querySelectorAll("input[type='checkbox']");
    Array.prototype.forEach.call(inputs, function (input) {
      input.checked = !!wanted[input.value];
    });
  }

  function setFastPreset() {
    setSelectedScales(["tiny", "small"]);
    els.runs.value = "1";
    els.warmup.value = "0";
    els.generateData.checked = true;
    els.includeOpensource.checked = true;
    els.multiprocess.checked = true;
  }

  function setFirstThreePreset() {
    setSelectedScales(["tiny", "small"]);
  }

  function renderLogs(logs) {
    var lines = logs || [];
    els.logOutput.textContent = lines.join("\n");
    els.logOutput.scrollTop = els.logOutput.scrollHeight;
  }

  function renderSummary(snapshot) {
    var summary = snapshot.summary || {};
    var selected = snapshot.selected_scales || [];
    var total = summary.total_scales || selected.length || 0;
    var passed = summary.passed_scales || 0;
    var failed = summary.failed_scales || 0;
    var skipped = summary.skipped_scales || 0;
    var completed = passed + failed + skipped;
    var running = snapshot.status === "running";

    els.jobStatus.textContent = badgeLabel(snapshot.status);
    els.jobStatus.className = statusClass(snapshot.status);

    els.currentScale.textContent = snapshot.current_scale || "-";
    els.currentStage.textContent = stageLabel(snapshot.current_stage || "-");
    els.sessionRoot.textContent = formatPath(snapshot.session_root);
    els.progressText.textContent = completed + " / " + total + " 个规模已完成";

    var pct = total > 0 ? Math.round((completed / total) * 100) : 0;
    els.progressBar.style.width = pct + "%";

    els.substatus.textContent = snapshot.message || "就绪";

    var env = snapshot.environment || {};
    var opensourceText = env.opensource_supported ? "可用" : "不可用";
    els.serverSummary.textContent = [
      "Py2：" + (env.python27_ready ? "已检测到" : "未检测到"),
      "Py3：" + (env.python3_ready ? "已检测到" : "未检测到"),
      "开源库：" + opensourceText,
      "输出根目录：" + formatPath(env.base_output_dir),
    ].join(" | ");

    els.startButton.disabled = running;
    els.stopButton.disabled = !running;
    els.presetFirstThree.disabled = running;
    els.presetFast.disabled = running;
  }

  function renderConfig(snapshot) {
    var config = snapshot.config || {};
    if (!bootstrapped) {
      els.python27Path.value = config.python27_path || "";
      els.python3Path.value = config.python3_path || "";
      els.outputBaseDir.value = config.output_base_dir || "";
      els.runs.value = config.runs != null ? config.runs : 3;
      els.warmup.value = config.warmup != null ? config.warmup : 1;
      els.mpWorkers.value = config.mp_workers != null ? config.mp_workers : 4;
      els.generateData.checked = config.generate_data !== false;
      els.includeOpensource.checked = config.include_opensource !== false;
      els.multiprocess.checked = config.multiprocess !== false;
      setSelectedScales(snapshot.selected_scales && snapshot.selected_scales.length ? snapshot.selected_scales : ["tiny", "small"]);

      if (!config.opensource_supported) {
        els.includeOpensource.checked = false;
        els.includeOpensource.disabled = true;
      }

      bootstrapped = true;
    }
  }

  function renderTable(snapshot) {
    var scales = snapshot.scales || [];
    els.scaleTableBody.innerHTML = "";

    if (!scales.length) {
      var tr = document.createElement("tr");
      var td = document.createElement("td");
      td.colSpan = 7;
      td.innerHTML = "<span class='badge badge-pending'>尚未开始</span><div class='badge-sub'>点击“开始验证”后，这里会显示各规模的阶段状态。</div>";
      tr.appendChild(td);
      els.scaleTableBody.appendChild(tr);
      return;
    }

    scales.forEach(function (scaleState) {
      els.scaleTableBody.appendChild(scaleRow(scaleState));
    });
  }

  function render(snapshot) {
    state = snapshot;
    renderConfig(snapshot);
    renderSummary(snapshot);
    renderTable(snapshot);
    renderLogs(snapshot.logs || []);
  }

  function refreshState() {
    return apiGet("/api/state").then(function (snapshot) {
      render(snapshot);
      return snapshot;
    }).catch(function (err) {
      els.substatus.textContent = err.message;
      els.jobStatus.textContent = "错误";
      els.jobStatus.className = "pill";
      return null;
    });
  }

  function collectPayload() {
    return {
      python27_path: els.python27Path.value.trim(),
      python3_path: els.python3Path.value.trim(),
      output_base_dir: els.outputBaseDir.value.trim(),
      runs: parseInt(els.runs.value, 10) || 1,
      warmup: parseInt(els.warmup.value, 10) || 0,
      mp_workers: parseInt(els.mpWorkers.value, 10) || 4,
      generate_data: els.generateData.checked,
      include_opensource: els.includeOpensource.checked,
      multiprocess: els.multiprocess.checked,
      selected_scales: selectedScales(),
    };
  }

  function startJob() {
    var payload = collectPayload();
    apiPost("/api/start", payload).then(function (result) {
      els.substatus.textContent = "任务 " + result.job_id + " 已启动";
      return refreshState();
    }).catch(function (err) {
      els.substatus.textContent = err.message;
    });
  }

  function stopJob() {
    apiPost("/api/stop", {}).then(function () {
      els.substatus.textContent = "已请求停止";
      return refreshState();
    }).catch(function (err) {
      els.substatus.textContent = err.message;
    });
  }

  function setupEvents() {
    els.startButton.addEventListener("click", startJob);
    els.stopButton.addEventListener("click", stopJob);
    els.refreshButton.addEventListener("click", refreshState);
    els.presetFast.addEventListener("click", setFastPreset);
    els.presetFirstThree.addEventListener("click", setFirstThreePreset);
  }

  function startPolling() {
    if (pollTimer) {
      window.clearInterval(pollTimer);
    }
    pollTimer = window.setInterval(function () {
      refreshState();
    }, 1200);
  }

  setupEvents();
  startPolling();
  refreshState();
})();
