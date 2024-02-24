from PIL import Image, ImageDraw, ImageFont, ImageChops
import numpy as np
import subprocess
import os
import cv2

cjpeg = "/opt/mozjpeg/bin/cjpeg"
cjpeg = "~/encoding/mozjpeg/build/cjpeg"
outfolder = "images"

gbricc = "magick $1 +profile icm -profile sRGB.icm -profile gbr.icc"

scale = 1
if scale < 1:
  small = ".small"
else:
  small = ""

font = ImageFont.truetype("arial.ttf", 512 * scale)
font2 = ImageFont.truetype("arial.ttf", 256 * scale)

h = int(128 * scale)
w = int(4096 * scale)

im = Image.new("RGBA", (w, w), (255, 255, 255, 255))
draw = ImageDraw.Draw(im)
draw.text((h, 1280 * scale + h), "R", fill=(255, 0, 0), font=font)
draw.text((h + font.getlength("R"), 1280 * scale + h),
          "G",
          fill=(0, 255, 0),
          font=font)
draw.text((h + font.getlength("RG"), 1280 * scale + h),
          "B",
          fill=(0, 0, 255),
          font=font)

alpha = Image.new("RGBA", (w, w), (0, 0, 0, 0))
drawa = ImageDraw.Draw(alpha)
drawa.text((h + font.getlength("RGB"), 1280 * scale + h),
           "A",
           fill=(255, 255, 255, 255),
           font=font)

im = np.array(im) - np.array(alpha)

s = int((w - h * 2) / 3)
y = w - h * 10 - h

grada = cv2.resize(np.linspace(0, 255, w - h * 2), (h, w - h * 2)).T
gradb = cv2.resize(np.linspace(255, 0, w - h * 2), (h, w - h * 2)).T
gradc = cv2.resize(np.linspace(0, 255, s), (h, s)).T

# screentone size 1 gap 1

im[y - h * 3:y - h * 2:2, h:h + s:2, 0:3] = 0

im[y - h * 3:y - h * 2, h + s:h + s * 2, 0] = gradc
im[y - h * 3:y - h * 2, h + s:h + s * 2, 1] = gradc
im[y - h * 3:y - h * 2, h + s:h + s * 2, 2] = gradc
im[y - h * 3:y - h * 2:2, h + s:h + s * 2:2, 0:3] = 255

im[y - h * 3:y - h * 2, h + s * 2:h + s * 3, 0] = gradc
im[y - h * 3:y - h * 2, h + s * 2:h + s * 3, 1] = gradc
im[y - h * 3:y - h * 2, h + s * 2:h + s * 3, 2] = gradc
im[y - h * 3:y - h * 2:2, h + s * 2:h + s * 3:2, 0:3] = 0

# screentone size 1 gap 2

im[y - h * 2:y - h * 1:3, h:h + s:3, 0:3] = 0

im[y - h * 2:y - h * 1, h + s:h + s * 2, 0] = gradc
im[y - h * 2:y - h * 1, h + s:h + s * 2, 1] = gradc
im[y - h * 2:y - h * 1, h + s:h + s * 2, 2] = gradc
im[y - h * 2:y - h * 1:3, h + s:h + s * 2:3, 0:3] = 255

im[y - h * 2:y - h * 1, h + s * 2:h + s * 3, 0] = gradc
im[y - h * 2:y - h * 1, h + s * 2:h + s * 3, 1] = gradc
im[y - h * 2:y - h * 1, h + s * 2:h + s * 3, 2] = gradc
im[y - h * 2:y - h * 1:3, h + s * 2:h + s * 3:3, 0:3] = 0

# screentone size 2 gap 2

im[y - h * 1 + 0:y - h * 0:4, h + 0:h + s:4, 0:3] = 0
im[y - h * 1 + 0:y - h * 0:4, h + 1:h + s:4, 0:3] = 0
im[y - h * 1 + 1:y - h * 0:4, h + 0:h + s:4, 0:3] = 0
im[y - h * 1 + 1:y - h * 0:4, h + 1:h + s:4, 0:3] = 0

im[y - h * 1:y - h * 0, h + s:h + s * 2, 0] = gradc
im[y - h * 1:y - h * 0, h + s:h + s * 2, 1] = gradc
im[y - h * 1:y - h * 0, h + s:h + s * 2, 2] = gradc

im[y - h * 1 + 0:y - h * 0:4, h + s + 0:h + s * 2:4, 0:3] = 0
im[y - h * 1 + 0:y - h * 0:4, h + s + 1:h + s * 2:4, 0:3] = 0
im[y - h * 1 + 1:y - h * 0:4, h + s + 0:h + s * 2:4, 0:3] = 0
im[y - h * 1 + 1:y - h * 0:4, h + s + 1:h + s * 2:4, 0:3] = 0

im[y - h * 1:y - h * 0, h + s * 2:h + s * 3, 0] = gradc
im[y - h * 1:y - h * 0, h + s * 2:h + s * 3, 1] = gradc
im[y - h * 1:y - h * 0, h + s * 2:h + s * 3, 2] = gradc

im[y - h * 1 + 0:y - h * 0:4, h + s * 2 + 0:h + s * 3:4, 0:3] = 255
im[y - h * 1 + 0:y - h * 0:4, h + s * 2 + 1:h + s * 3:4, 0:3] = 255
im[y - h * 1 + 1:y - h * 0:4, h + s * 2 + 0:h + s * 3:4, 0:3] = 255
im[y - h * 1 + 1:y - h * 0:4, h + s * 2 + 1:h + s * 3:4, 0:3] = 255
# colors

im[y + h * 0:y + h * 1, h:-h, 0:3] = 0
im[y + h * 0:y + h * 1, h:-h, 0] = grada

im[y + h * 1:y + h * 2, h:-h, 1] = grada
im[y + h * 1:y + h * 2, h:-h, 2] = grada

im[y + h * 2:y + h * 3, h:-h, 0:3] = 0
im[y + h * 2:y + h * 3, h:-h, 1] = grada

im[y + h * 3:y + h * 4, h:-h, 0] = grada
im[y + h * 3:y + h * 4, h:-h, 2] = grada

im[y + h * 4:y + h * 5, h:-h, 0:3] = 0
im[y + h * 4:y + h * 5, h:-h, 2] = grada

im[y + h * 5:y + h * 6, h:-h, 0] = grada
im[y + h * 5:y + h * 6, h:-h, 1] = grada

im[y + h * 6:y + h * 7, h:-h, 0] = grada
im[y + h * 6:y + h * 7, h:-h, 1] = grada
im[y + h * 6:y + h * 7, h:-h, 2] = grada

im[y + h * 7:y + h * 8, h:-h, 0] = gradb
im[y + h * 7:y + h * 8, h:-h, 1] = gradb
im[y + h * 7:y + h * 8, h:-h, 2] = gradb

im[y + h * 8:y + h * 9, h:-h, 0:3] = 0
im[y + h * 8:y + h * 9, h:-h, 3] = gradb

im[y + h * 9:y + h * 10, h:-h, 0:3] = 0
im[y + h * 9:y + h * 10, h:-h, 3] = grada

im = Image.fromarray(im)

draw = ImageDraw.Draw(im)

draw.text((2048 * scale, 1280 * scale + h), "C", fill=(0, 255, 255), font=font)
draw.text((2048 * scale + font.getlength("C"), 1280 * scale + h),
          "M",
          fill=(255, 0, 255),
          font=font)
draw.text((2048 * scale + font.getlength("CM"), 1280 * scale + h),
          "Y",
          fill=(255, 255, 0),
          font=font)
draw.text((2048 * scale + font.getlength("CMY"), 1280 * scale + h),
          "K",
          fill=(0, 0, 0),
          font=font)

ims = im.copy()

# yapf: disable
formats = [
    ("RGBA", "PNG", "RGBA"),
    ("RGBA gbr", "PNG", "RGBA", f"{gbricc} $1", "png", True),
    ("RGB", "PNG", "RGB"),
    ("RGB gbr", "PNG", "RGB", f"{gbricc} $1", "png", True),
    ("LA", "PNG", "LA"),
    ("L", "PNG", "L"),
    ("RGB", "JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -rgb -progressive $1"),
    ("YCbCr444 gbr", "JPEG", "RGB", f"{gbricc} $2.jpg", "png", False),
    ("YCbCr420", "JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -progressive $1"),
    ("YCbCr422", "JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -sample 2x1 -progressive $1"),
    ("YCbCr440", "JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -sample 1x2 -progressive $1"),
    ("YCbCr444", "JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -sample 1x1 -progressive $1"),
    ("XYB", "JPEG jpegli", "RGB", f"cjpegli $1 --xyb $2.jpg"),
    ("YCCK", "JPEG", "RGB", f"convert $1 -colorspace CMYK $2.jpg && exiftool \"-icc_profile<=USWebCoatedSWOP.icc\" $2.jpg && rm $2.jpg_original"),
    ("CMYK", "JPEG", "CMYK", "exiftool \"-icc_profile<=USWebCoatedSWOP.icc\" $1 && rm $1_original", "jpg", True),
    ("YCCK no ICC", "JPEG", "RGB", f"convert $1 -colorspace CMYK $2.jpg"),
    ("CMYK no ICC", "JPEG", "CMYK", None, "jpg", True),
    ("L", "JPEG", "L", f"{cjpeg} -outfile $2.jpg -grayscale -progressive $1"),
    ("RGBA", "WEBP", "RGBA", "cwebp $1 -o $2.webp"),
    ("RGBA gbr", "WEBP", "RGBA", f"{gbricc} $2.webp"),
    ("RGBA", "WEBP_LOSSLESS", "RGBA", "cwebp $1 -lossless -o $2.webp"),
    ("RGB", "WEBP", "RGB", "cwebp $1 -o $2.webp"),
    ("RGB", "WEBP_LOSSLESS", "RGB", "cwebp $1 -lossless -o $2.webp"),
    ("L", "WEBP", "L", "cwebp $1 -o $2.webp"),
    ("L", "WEBP_LOSSLESS", "L", "cwebp $1 -lossless -o $2.webp"),
    ("LA", "WEBP", "LA", "cwebp $1 -o $2.webp"),
    ("LA", "WEBP_LOSSLESS", "LA", "cwebp $1 -lossless -o $2.webp"),
    ("RGBA", "AVIF", "RGBA", "avifenc $1 -o $2.avif"),
    #("RGBA gbr", "AVIF", "RGBA", f"{gbricc} $2.avif"),
    ("RGB", "AVIF", "RGB", "avifenc $1 -o $2.avif"),
    ("L", "AVIF", "L", "avifenc $1 -o $2.avif"),
    ("LA", "AVIF", "LA", "avifenc $1 -o $2.avif"),
    ("YCbCr420", "JXL_JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -progressive $1 && cjxl $2.jpg --lossless_jpeg=1 $2.jxl && rm $2.jpg"),
    ("L", "JXL_JPEG", "L", f"{cjpeg} -outfile $2.jpg -grayscale -progressive $1 && cjxl $2.jpg --lossless_jpeg=1 $2.jxl && rm $2.jpg"),
    ("RGB", "JXL_VarDCT", "RGB", "cjxl $1 $2.jxl"),
    ("RGBA", "JXL_VarDCT", "RGBA", "cjxl $1 $2.jxl"),
    ("LA", "JXL_VarDCT", "LA", "cjxl $1 $2.jxl"),
    ("L", "JXL_VarDCT", "L", "cjxl $1 $2.jxl"),
    ("RGB", "JXL_Modular", "RGB", "cjxl $1 --modular=1 $2.jxl"),
    ("RGBA", "JXL_Modular", "RGBA", "cjxl $1 --modular=1 $2.jxl"),
    ("LA", "JXL_Modular", "LA", "cjxl $1 --modular=1 $2.jxl"),
    ("L", "JXL_Modular", "L", "cjxl $1 --modular=1 $2.jxl"),
]
# yapf: enable

for fs in formats:
  if len(fs) == 6:
    [color, fmt, colormode, cmd, ext, keep] = fs
  else:
    ext = "png"
    keep = False

  if len(fs) == 4:
    [color, fmt, colormode, cmd] = fs
  if len(fs) == 3:
    [color, fmt, colormode] = fs
    cmd = None

  im = ims.copy()

  draw = ImageDraw.Draw(im)
  draw.text((h, h), fmt, fill=(0, 0, 0), font=font)
  draw.text((h, 512 * scale + h), color, fill=(0, 0, 0), font=font)

  if scale < 1:
    draw.text((h, h + 1024 * scale), "small", fill=(0, 0, 0), font=font2)

  im.convert(colormode).save(os.path.join(outfolder, f"{fmt}.{color}{small}.{ext}"))

  if cmd:
    cmdr = cmd.replace("$1", os.path.join(outfolder,
                                          f"\"{fmt}.{color}{small}.{ext}\""))
    cmdr = cmdr.replace("$2", os.path.join(outfolder, f"\"{fmt}.{color}{small}\""))
    if subprocess.run(cmdr, shell=True).returncode != 0: exit(1)
    if not keep:
      os.remove(os.path.join(outfolder, f"{fmt}.{color}{small}.{ext}"))

  continue

  im = im.resize((1024, 1024))

  im.convert(colormode).save(
      os.path.join(outfolder, f"{fmt}.{color}.small.{ext}"))

  if cmd:
    cmdr = cmd.replace(
        "$1", os.path.join(outfolder, f"\"{fmt}.{color}.small.{ext}\""))
    cmdr = cmdr.replace("$2",
                        os.path.join(outfolder, f"\"{fmt}.{color}.small\""))
    if subprocess.run(cmdr, shell=True).returncode != 0: exit(1)
    if not keep:
      os.remove(os.path.join(outfolder, f"{fmt}.{color}.small.{ext}"))
