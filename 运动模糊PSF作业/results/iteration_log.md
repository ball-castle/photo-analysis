# 本次实际对照记录（摘要）

- 测试先于实现运行：`motion_psf` 未定义，MATLAB 报“无法识别函数”。
- 第一版距离采样实现：`LEN=9, THETA=45°` 的矩阵尺寸断言失败；初稿支持域按代码计算为 11×11，内置函数为 7×7。
- 修正为 R2023b 半核与端点算法后：104 组参数和 2 种默认调用通过 `isequal`。
- `Maximum absolute element-wise error: 0`。
- MATLAB version: `23.2.0.2365128 (R2023b)`。
