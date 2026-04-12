(function () {
  "use strict";

  var state = null;
  var bootstrapped = false;
  var pollTimer = null;
  var allLogs = [];
  var logFilter = "";
  var activeLogTag = null;

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
    logSearch: document.getElementById("log-search"),
    logFilters: document.getElementById("log-filters"),
    logCopy: document.getElementById("log-copy"),
    logClear: document.getElementById("log-clear"),
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
    presetDefaultTwo: document.getElementById("preset-default-two"),
    presetFast: document.getElementById("preset-fast"),
    scaleList: document.getElementById("scale-list"),
    resultsPanel: document.getElementById("results-panel"),
    resultsToolbar: document.getElementById("results-toolbar"),
    resultsPreview: document.getElementById("results-preview"),
  };

  var stageOrder = ["py2", "py3", "os", "analysis", "validation"];
  var stageLabels = {
    py2: "Py2",
    py3: "Py3",
    os: "开源库",
    analysis: "分析",
    validation: "校验",
  };
  var stageWeights = {
    py2: 0.2,
    py3: 0.2,
    os: 0.2,
    analysis: 0.2,
    validation: 0.2,
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

  function errorTooltip(stage) {
    if (!stage || !stage.output_tail || !stage.output_tail.length) {
      return "";
    }
    var tail = stage.output_tail.slice(-3);
    return tail.join("\n");
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

      var tooltip = errorTooltip(stage);
      if (tooltip) {
        badge.setAttribute("title", tooltip);
        badge.style.cursor = "help";
      }

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

  function setDefaultTwoScalesPreset() {
    setSelectedScales(["tiny", "small"]);
  }

  function computeGranularProgress(snapshot) {
    var scales = snapshot.scales || [];
    var selected = snapshot.selected_scales || [];
    var total = selected.length || scales.length || 1;
    if (total === 0) {
      return 0;
    }

    var totalProgress = 0;
    scales.forEach(function (scale) {
      var scaleProgress = 0;
      stageOrder.forEach(function (stageName) {
        var stage = scale.stages ? scale.stages[stageName] : null;
        var status = stage ? stage.status : "pending";
        if (status === "passed" || status === "failed" || status === "stopped" || status === "skipped") {
          scaleProgress += stageWeights[stageName] || 0.2;
        } else if (status === "running") {
          scaleProgress += (stageWeights[stageName] || 0.2) * 0.5;
        }
      });
      totalProgress += Math.min(scaleProgress, 1) / total;
    });

    return Math.max(0, Math.min(100, Math.round(totalProgress * 100)));
  }

  function extractLogTags(lines) {
    var tags = {};
    lines.forEach(function (line) {
      var m = line.match(/^\[(\d{2}:\d{2}:\d{2})\]\s*\[([^\]]+)\]/);
      if (m && m[2]) {
        tags[m[2].trim()] = true;
      }
    });
    return Object.keys(tags).sort();
  }

  function renderLogs(logs) {
    allLogs = logs || [];

    var lines = allLogs.filter(function (line) {
      var match = true;
      if (logFilter) {
        match = line.toLowerCase().indexOf(logFilter.toLowerCase()) !== -1;
      }
      if (match && activeLogTag) {
        match = line.indexOf("[" + activeLogTag + "]") !== -1;
      }
      return match;
    });

    els.logOutput.textContent = lines.join("\n");
    els.logOutput.scrollTop = els.logOutput.scrollHeight;

    var tags = extractLogTags(allLogs);
    renderLogTags(tags);
  }

  function renderLogTags(tags) {
    var existing = {};
    var buttons = els.logFilters.querySelectorAll(".log-filter");
    Array.prototype.forEach.call(buttons, function (b) {
      existing[b.textContent] = b;
    });

    tags.forEach(function (tag) {
      if (existing[tag]) {
        return;
      }
      var btn = document.createElement("span");
      btn.className = "log-filter" + (tag === activeLogTag ? " active" : "");
      btn.textContent = tag;
      btn.addEventListener("click", function () {
        activeLogTag = (activeLogTag === tag) ? null : tag;
        renderLogTagsState();
        renderLogs(allLogs);
      });
      els.logFilters.appendChild(btn);
    });
  }

  function renderLogTagsState() {
    var buttons = els.logFilters.querySelectorAll(".log-filter");
    Array.prototype.forEach.call(buttons, function (btn) {
      btn.classList.toggle("active", btn.textContent === activeLogTag);
    });
  }

  function renderResultsPanel(snapshot) {
    if (snapshot.status !== "completed" && snapshot.status !== "failed" && snapshot.status !== "stopped") {
      els.resultsPanel.style.display = "none";
      return;
    }

    var firstScale = (snapshot.scales || [])[0];
    if (!firstScale) {
      els.resultsPanel.style.display = "none";
      return;
    }

    var artifacts = firstScale.artifacts || {};
    var outputDir = firstScale.output_dir || "";
    var reportPath = artifacts["comparison_report.md"] ? artifacts["comparison_report.md"].path : "";
    var dataPath = artifacts["comparison_data.json"] ? artifacts["comparison_data.json"].path : "";

    els.resultsToolbar.innerHTML = "";

    if (outputDir) {
      var openBtn = document.createElement("button");
      openBtn.className = "ghost";
      openBtn.textContent = "打开结果文件夹";
      openBtn.addEventListener("click", function () {
        window.open("file:///" + outputDir.replace(/\\/g, "/"), "_blank");
      });
      els.resultsToolbar.appendChild(openBtn);
    }

    if (reportPath) {
      var dlReport = document.createElement("a");
      dlReport.className = "button ghost";
      dlReport.textContent = "下载 report.md";
      dlReport.href = "file:///" + reportPath.replace(/\\/g, "/");
      dlReport.download = "comparison_report.md";
      dlReport.style.textDecoration = "none";
      els.resultsToolbar.appendChild(dlReport);
    }

    if (dataPath) {
      var dlData = document.createElement("a");
      dlData.className = "button ghost";
      dlData.textContent = "下载 data.json";
      dlData.href = "file:///" + dataPath.replace(/\\/g, "/");
      dlData.download = "comparison_data.json";
      dlData.style.textDecoration = "none";
      els.resultsToolbar.appendChild(dlData);
    }

    if (reportPath) {
      fetch("file:///" + reportPath.replace(/\\/g, "/"))
        .then(function (res) { return res.text(); })
        .then(function (text) {
          var preview = text.split("\n").slice(0, 50).join("\n");
          if (text.split("\n").length > 50) {
            preview += "\n\n...（报告较长，请下载完整文件查看）";
          }
          els.resultsPreview.textContent = preview;
          els.resultsPanel.style.display = "block";
        })
        .catch(function () {
          els.resultsPreview.textContent = "报告文件存在但无法预览，请使用下载按钮打开。";
          els.resultsPanel.style.display = "block";
        });
    } else {
      els.resultsPreview.textContent = "未找到 comparison_report.md";
      els.resultsPanel.style.display = "block";
    }
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

    var pct = computeGranularProgress(snapshot);
    els.progressBar.style.width = pct + "%";

    var stageHint = "";
    if (running && snapshot.current_scale && snapshot.current_stage) {
      stageHint = "正在运行：" + snapshot.current_scale + " / " + stageLabel(snapshot.current_stage);
    }

    var sub = snapshot.message || "就绪";
    if (stageHint) {
      sub = stageHint + " · " + sub;
    }
    els.substatus.textContent = sub;

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
    els.presetDefaultTwo.disabled = running;
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
    renderResultsPanel(snapshot);
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
      els.resultsPanel.style.display = "none";
      return refreshState();
    }).catch(function (err) {
      els.substatus.textContent = err.message;
    });
  }

  function stopJob() {
    if (!confirm("确定要终止当前正在执行的基准测试吗？")) {
      return;
    }
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
    els.presetDefaultTwo.addEventListener("click", setDefaultTwoScalesPreset);

    els.logSearch.addEventListener("input", function () {
      logFilter = els.logSearch.value.trim();
      renderLogs(allLogs);
    });

    els.logClear.addEventListener("click", function () {
      allLogs = [];
      renderLogs([]);
    });

    els.logCopy.addEventListener("click", function () {
      var text = els.logOutput.textContent;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          els.logCopy.textContent = "已复制";
          window.setTimeout(function () {
            els.logCopy.textContent = "复制全部";
          }, 1200);
        });
      } else {
        var ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        els.logCopy.textContent = "已复制";
        window.setTimeout(function () {
          els.logCopy.textContent = "复制全部";
        }, 1200);
      }
    });
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
