# 实验图像来源与许可

两张输入均为 Unsplash 摄影师发布的真实人像，不是生成图像。访问日期：2026-10-08。原始下载文件保存在本目录，程序将其灰度化并按比例中心裁剪到正方形后缩放为 512×512。

| 本地文件 | 作者与页面 | 许可 | 实验用途 |
|---|---|---|---|
| `older_woman_wrinkles.jpg` | Alex Guillaume, [An older woman with wrinkles on her face](https://unsplash.com/photos/an-older-woman-with-wrinkles-on-her-face-mSh9yhcJk1A) | [Unsplash License](https://unsplash.com/license) | 暗调皱纹人脸，直方图均衡化与规定化 |
| `freckled_woman.jpg` | Robert Piosik, [Grayscale photo of a woman's face](https://unsplash.com/es/fotos/foto-en-escala-de-grises-de-la-cara-de-la-mujer-bJR4cvkfxf0) | [Unsplash License](https://unsplash.com/license) | 带雀斑人脸，边缘、加噪去噪和现代滤波 |

Unsplash 的许可页面说明图片可免费用于商业与非商业用途，且不强制署名；本项目仍保留摄影师与来源链接。实验中的 PSNR/SSIM 仅把未加噪原始像素作为人工加噪图像的干净参考，不将任一带雀斑或皱纹的人像当作无瑕疵皮肤真值。
