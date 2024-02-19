from PIL import Image, ImageDraw, ImageFont, ImageChops
import numpy as np
import subprocess
import os

cjpeg = "/opt/mozjpeg/bin/cjpeg"
cjpeg = "~/encoding/mozjpeg/build/cjpeg"
outfolder = "images"

font = ImageFont.truetype("arial.ttf", 256)

cmyk = Image.new("CMYK", (2048, 2048), (0, 0, 0, 0))
draw = ImageDraw.Draw(cmyk)

draw.text((64, 1024 + 64), "C", fill=(255, 0, 0, 0), font=font)
draw.text((64 + font.getlength("C"), 1024 + 64),
          "M",
          fill=(0, 255, 0, 0),
          font=font)
draw.text((64 + font.getlength("CM"), 1024 + 64),
          "Y",
          fill=(0, 0, 255, 0),
          font=font)
draw.text((64 + font.getlength("CMY"), 1024 + 64),
          "K",
          fill=(0, 0, 0, 255),
          font=font)
cmyks = cmyk.copy()

im = Image.new("RGBA", (2048, 2048), (255, 255, 255, 255))
draw = ImageDraw.Draw(im)
draw.text((64, 768 + 64), "R", fill=(255, 0, 0), font=font)
draw.text((64 + font.getlength("R"), 768 + 64),
          "G",
          fill=(0, 255, 0),
          font=font)
draw.text((64 + font.getlength("RG"), 768 + 64),
          "B",
          fill=(0, 0, 255),
          font=font)

alpha = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
drawa = ImageDraw.Draw(alpha)
drawa.text((64 + font.getlength("RGB"), 768 + 64),
           "A",
           fill=(255, 255, 255, 255),
           font=font)

im = Image.fromarray(np.array(im) - np.array(alpha))

draw = ImageDraw.Draw(im)

draw.text((64, 1024 + 64), "C", fill=(0, 255, 255), font=font)
draw.text((64 + font.getlength("C"), 1024 + 64),
          "M",
          fill=(255, 0, 255),
          font=font)
draw.text((64 + font.getlength("CM"), 1024 + 64),
          "Y",
          fill=(255, 255, 0),
          font=font)
draw.text((64 + font.getlength("CMY"), 1024 + 64),
          "K",
          fill=(0, 0, 0),
          font=font)

ims = im.copy()

# yapf: disable
formats = [
    ("RGBA", "AVIF", "RGBA", "avifenc $1 -o $2.avif"),
    ("RGB", "AVIF", "RGB", "avifenc $1 -o $2.avif"),
    ("L", "AVIF", "L", "avifenc $1 -o $2.avif"),
    ("LA", "AVIF", "LA", "avifenc $1 -o $2.avif"),
    ("RGBA", "WEBP", "RGBA", "cwebp $1 -o $2.webp"),
    ("RGBA", "WEBP_LOSSLESS", "RGBA", "cwebp $1 -lossless -o $2.webp"),
    ("RGB", "WEBP", "RGB", "cwebp $1 -o $2.webp"),
    ("RGB", "WEBP_LOSSLESS", "RGB", "cwebp $1 -lossless -o $2.webp"),
    ("L", "WEBP", "L", "cwebp $1 -o $2.webp"),
    ("L", "WEBP_LOSSLESS", "L", "cwebp $1 -lossless -o $2.webp"),
    ("LA", "WEBP", "LA", "cwebp $1 -o $2.webp"),
    ("LA", "WEBP_LOSSLESS", "LA", "cwebp $1 -lossless -o $2.webp"),
    ("RGBA", "PNG", "RGBA"),
    ("RGB", "PNG", "RGB"),
    ("LA", "PNG", "LA"),
    ("L", "PNG", "L"),
    ("RGB", "JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -rgb -progressive $1"),
    ("YCbCr420", "JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -progressive $1"),
    ("YCbCr422", "JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -sample 2x1 -progressive $1"),
    ("YCbCr440", "JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -sample 1x2 -progressive $1"),
    ("YCbCr444", "JPEG", "RGB", f"{cjpeg} -outfile $2.jpg -sample 1x1 -progressive $1"),
    ("XYB", "JPEG jpegli", "RGB", f"cjpegli $1 --xyb $2.jpg"),
    ("CMYK", "JPEG", "RGB", f"convert $1 -colorspace CMYK $2.jpg"),
    ("CMYK", "JPEG", "RGB"),
    ("L", "JPEG", "L", f"{cjpeg} -outfile $2.jpg -grayscale -progressive $1"),
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
  if len(fs) == 4:
    [color, fmt, colormode, cmd] = fs
  if len(fs) == 3:
    [color, fmt, colormode] = fs
    cmd = None

  #if color == "CMYK":
  #  im = cmyks.copy()
  #else:
  im = ims.copy()

  draw = ImageDraw.Draw(im)
  draw.text((64, 64), fmt, fill=(0, 0, 0), font=font)
  draw.text((64, 256 + 64), color, fill=(0, 0, 0), font=font)

  #if color == "CMYK":
  #  im.save(os.path.join(outfolder, f"{fmt}.{color}.jpg"))
  #else:
  im.convert(colormode).save(os.path.join(outfolder, f"{fmt}.{color}.png"))

  if cmd:
    cmd = cmd.replace("$1", os.path.join(outfolder, f"\"{fmt}.{color}.png\""))
    cmd = cmd.replace("$2", os.path.join(outfolder, f"\"{fmt}.{color}\""))
    subprocess.run(cmd, shell=True)
    os.remove(os.path.join(outfolder, f"{fmt}.{color}.png"))