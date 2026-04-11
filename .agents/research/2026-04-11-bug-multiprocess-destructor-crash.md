# Bug Report: Python 2 退出时 VC++ Runtime abnormal termination

## 症状
- 在 `C:\Python27\ArcGIS10.8\python.exe` 下，`MP_*` 相关基准跑完后，控制台已经打印 `teardown() 完成`，随后弹出 `Microsoft Visual C++ Runtime Library`，提示 `abnormal program termination`。
- 这说明崩溃发生在进程退出/对象析构阶段，而不是正常的 Python 异常路径。

## 根因
- 触发点是多进程基准类里的 `__del__()` 析构器。
- 历史上，这些析构器位于：
  - `benchmarks/multiprocess_tests.py:221-225`
  - `benchmarks/multiprocess_tests.py:387-391`
  - `benchmarks/multiprocess_tests.py:503-507`
  - `benchmarks/multiprocess_tests.py:639-643`
  - `benchmarks/multiprocess_tests.py:772-776`
  - `benchmarks/multiprocess_benchmark.py:154-161`
- 它们在解释器退出时再次调用 `self.teardown()` / 清理逻辑，ArcPy 和原生运行时在 shutdown 阶段已经处于不稳定状态，导致 Python 2 进程直接被 VC++ runtime 终止。
- 设计上，这些析构器是为了补 `setup()` 不在 `try/finally` 里的缺口，但这种补救方式本身是高风险的。

## 模式对比
- 正常基线是 `benchmarks/base_benchmark.py` 的显式 `try/finally` 收尾，而不是依赖析构器。
- `multiprocess_tests_os.py` 没有析构器，但同样把 `setup()` 放在 `try` 外面，所以我也把它一起改成了对称结构，避免以后再出现同类收尾缺口。

## 修复
- 删除了 `benchmarks/multiprocess_tests.py` 和 `benchmarks/multiprocess_benchmark.py` 中所有 `__del__()`。
- 把 `setup()` 移进 `try/finally` 保护范围，确保 setup 失败时也会走正常清理，而不是靠析构器补救。
- 保留并前置了文件级临时输出清理：
  - `benchmarks/multiprocess_benchmark.py` 的 `cleanup_temp_files()` 仍在 `finally` 中执行。
- 同步修复了：
  - `benchmarks/base_benchmark.py`
  - `benchmarks/multiprocess_tests_os.py`

## 验证
- `python -X utf8 -m py_compile`：通过。
- 导入烟雾测试：
  - `import run_benchmarks`
  - `import benchmarks.multiprocess_tests`
  - `import benchmarks.multiprocess_benchmark`
  - `import benchmarks.multiprocess_tests_os`
  - 输出：`imports-ok`
- `git diff --check`：通过。
- `rg -n "def __del__" -g "*.py"`：无结果，确认仓库里不再残留这些析构器。

## 结论
- 这是一个典型的“用 `__del__()` 补 cleanup”导致的退出期 native 崩溃。
- 根治方式不是继续加更多兜底析构器，而是把清理收口到显式 `try/finally`，并避免在 interpreter shutdown 阶段再碰 ArcPy。
