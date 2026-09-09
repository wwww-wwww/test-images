# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "numpy>=2.5.2",
#     "opencv-python>=5.0.0.93",
#     "pillow>=12.3.0",
# ]
# ///
"""Generate HDR test images.

The pattern is an ordinary SDR image apart from one disc above the pepper: the
disc carries concentric rings from 203 nits at the rim up to 10000 nits at the
centre, so that only a small portion of the frame exceeds SDR white.

Output is images/hdr/NNN.ext, numbered from 000 in the order of the formats
table at the bottom; each image names its own format and colour encoding.

The pattern is authored as an SDR sRGB base image plus a linear-light boost map,
so the same content drives the gain map encoders (base + HDR intent) and the
single layer PQ/HLG encoders (base * boost, converted to nits).
"""

import os
import subprocess
import time
from functools import partial

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

avifenc = os.path.expanduser("~/encoding/libavif/build/avifenc")
avifgainmaputil = os.path.expanduser("~/encoding/libavif/build/avifgainmaputil")
cjxl = os.path.expanduser("~/encoding/libjxl/build/tools/cjxl")
ultrahdr_app = os.path.expanduser("~/encoding/libultrahdr/build/ultrahdr_app")
# writing the AVIF container needs libultrahdr built against a libheif with the
# ISO 21496-1 gain map API, i.e. -DUHDR_ENABLE_HEIF=1 -DUHDR_BUILD_DEPS=1
ultrahdr_app_heif = os.path.expanduser("~/encoding/libultrahdr/build-heif/ultrahdr_app")

outfolder = "images/hdr"
tmpfolder = "images/hdr/tmp"

SDR_WHITE = 203.0  # nits, reference white of the SDR base image
HLG_PEAK = 1000.0  # nits, HLG nominal peak display luminance

w = 2048
scale = w / 4096
h = int(128 * scale)

font = ImageFont.truetype("arial.ttf", int(512 * scale))
font3 = ImageFont.truetype("arial.ttf", int(128 * scale))
font4 = ImageFont.truetype("arial.ttf", int(64 * scale))

# luminance of the disc rings, from the rim inwards
disc_nits = [203, 400, 600, 1000, 2000, 4000, 10000]

# sRGB/BT.709 D65 -> BT.2020 D65
RGB_TO_2020 = np.array(
    [
        [0.6274039, 0.3292830, 0.0433131],
        [0.0690973, 0.9195404, 0.0113623],
        [0.0163915, 0.0880132, 0.8955953],
    ]
)
LUMA_2020 = np.array([0.2627, 0.6780, 0.0593])


def srgb_to_linear(x):
    x = x.astype(np.float32) / 255
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def pq_oetf(y):
    """Absolute luminance normalised to 10000 nits -> PQ signal."""
    m1, m2 = 0.1593017578125, 78.84375
    c1, c2, c3 = 0.8359375, 18.8515625, 18.6875
    yp = np.clip(y, 0, 1) ** m1
    return ((c1 + c2 * yp) / (1 + c3 * yp)) ** m2


def hlg_oetf(e):
    """Scene linear normalised to [0,1] -> HLG signal."""
    a, b, c = 0.17883277, 0.28466892, 0.55991073
    e = np.clip(e, 0, 1)
    return np.where(
        e <= 1 / 12, np.sqrt(3 * e), a * np.log(np.maximum(12 * e - b, 1e-6)) + c
    )


def nits_to_pq(nits):
    return pq_oetf(nits / 10000)


def nits_to_hlg(nits):
    """Display referred nits -> HLG signal, undoing the reference OOTF."""
    disp = np.clip(nits / HLG_PEAK, 0, 1)
    gamma = 1.2  # reference OOTF system gamma at a 1000 nit peak
    y = np.tensordot(disp, LUMA_2020, axes=([-1], [0]))[..., None]
    scene = disp * np.where(y > 0, np.maximum(y, 1e-6) ** ((1 - gamma) / gamma), 0)
    return hlg_oetf(scene)


def to_2020_nits(sdr, boost):
    """SDR sRGB base + linear light boost map -> BT.2020 linear nits."""
    lin = srgb_to_linear(sdr) * boost[..., None]
    return (lin @ RGB_TO_2020.T) * SDR_WHITE


def write_png16(path, rgb):
    u16 = np.clip(rgb * 65535 + 0.5, 0, 65535).astype(np.uint16)
    cv2.imwrite(path, u16[..., ::-1])


def pattern(fmt, desc):
    """Returns (sdr uint8 HxWx3, boost float32 HxW)."""
    im = Image.new("RGB", (w, w), (255, 255, 255))
    draw = ImageDraw.Draw(im)

    pepper = Image.open("GIMP_Pepper.png")
    pepper = pepper.resize((int(pepper.width * scale), int(pepper.height * scale)))
    ppx, ppy = int(w * 0.86), int(w * 0.42)
    im.paste(pepper, (ppx, ppy), pepper)

    ty = h
    for text, f in [
        (fmt, font),
        (desc, font3),
        (str(int(time.time())), font3),
        ("HDR disc above the pepper, rings from the rim inwards:", font4),
        (" / ".join(str(n) for n in disc_nits) + " nits", font4),
    ]:
        draw.text((h, ty), text, fill=(0, 0, 0), font=f)
        ty += f.size * 5 // 4

    # RGB / CMY headline
    ty = int(1280 * scale + h)
    for i, (ch, col) in enumerate(
        [("R", (255, 0, 0)), ("G", (0, 255, 0)), ("B", (0, 0, 255))]
    ):
        draw.text((h + font.getlength("RGB"[:i]), ty), ch, fill=col, font=font)
    for i, (ch, col) in enumerate(
        [("C", (0, 255, 255)), ("M", (255, 0, 255)), ("Y", (255, 255, 0))]
    ):
        draw.text(
            (2048 * scale + font.getlength("CMY"[:i]), ty), ch, fill=col, font=font
        )

    sdr = np.array(im)
    boost = np.ones((w, w), np.float32)

    x0, x1 = h, w - h
    span = x1 - x0

    # the only part of the frame that goes above SDR white: a white disc above
    # the pepper, with concentric rings stepping from the rim to the centre
    r = h * 3
    cx = min(ppx + pepper.width // 2, x1 - r)
    cy = ppy - h // 4 - r
    box = (slice(cy - r, cy + r + 1), slice(cx - r, cx + r + 1))
    yy, xx = np.mgrid[cy - r : cy + r + 1, cx - r : cx + r + 1]
    dist = np.hypot(xx - cx, yy - cy)
    disc, ring = sdr[box], boost[box]
    disc[dist <= r] = 255
    for i, nits in enumerate(disc_nits):
        ring[dist <= r * (1 - i / len(disc_nits))] = nits / SDR_WHITE
    disc[np.abs(dist - r) < max(h // 32, 1)] = 0  # outline, stays SDR
    ring[np.abs(dist - r) < max(h // 32, 1)] = 1

    # SDR step wedge
    wy = int(w - h * 13)
    wh = h * 2
    steps = 8
    sw = span // steps
    for i in range(steps):
        xa = x0 + i * sw
        xb = x1 if i == steps - 1 else xa + sw
        sdr[wy : wy + wh, xa:xb] = round(i * 255 / (steps - 1))

    # SDR grey ramp
    ry = wy + wh + h
    rh = h * 2
    grad = np.linspace(0, 255, span, dtype=np.float32)
    sdr[ry : ry + rh, x0:x1] = grad[None, :, None]

    # SDR per channel gradients
    gy = ry + rh + h
    for i, mask in enumerate([(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 1)]):
        ya = gy + i * h
        sdr[ya : ya + h, x0:x1] = 0
        for c in range(3):
            if mask[c]:
                sdr[ya : ya + h, x0:x1, c] = grad

    im = Image.fromarray(sdr)
    draw = ImageDraw.Draw(im)
    for ya, yb in [(wy, wy + wh), (ry, ry + rh)]:
        draw.rectangle(
            [x0, ya, x1 - 1, yb - 1], outline=(0, 0, 0), width=max(h // 64, 1)
        )
    for i in range(steps):
        v = round(i * 255 / (steps - 1))
        draw.text(
            (x0 + i * sw + h // 4, wy + h // 2),
            str(v),
            fill=(0, 0, 0) if v > 127 else (255, 255, 255),
            font=font3,
        )

    return np.array(im), boost


def run(cmd):
    print("+", cmd)
    if subprocess.run(cmd, shell=True).returncode != 0:
        raise SystemExit(1)


def q(path):
    return '"' + path + '"'


def single_layer(fmt, desc, out, transfer):
    """Single layer PQ / HLG AVIF or JXL."""
    sdr, boost = pattern(fmt, desc)
    nits = to_2020_nits(sdr, boost)
    if transfer == "pq":
        signal = nits_to_pq(nits)
        cicp_t, jxl_t = 16, "PeQ"
        peak = 10000
    else:
        signal = nits_to_hlg(nits)
        cicp_t, jxl_t = 18, "HLG"
        peak = HLG_PEAK
    maxcll = int(min(nits.max(), peak))
    maxpall = int(np.clip(nits @ LUMA_2020, 0, peak).mean())

    src = os.path.join(tmpfolder, os.path.basename(out) + ".png")
    write_png16(src, signal)

    if out.endswith(".avif"):
        run(
            f"{q(avifenc)} --cicp 9/{cicp_t}/9 -d 10 -y 444 -q 90 -s 4"
            f" --clli {maxcll},{maxpall} {q(src)} -o {q(out)}"
        )
    else:
        run(
            f"{q(cjxl)} {q(src)} {q(out)} -d 1 -e 7"
            f" -x color_space=RGB_D65_202_Rel_{jxl_t}"
        )
    os.remove(src)


def gainmap(fmt, desc, out):
    """UltraHDR gain map image: sRGB base plus a BT.2100 PQ HDR intent."""
    app = ultrahdr_app
    if out.endswith(".avif"):
        if not os.path.exists(ultrahdr_app_heif):
            print(f"skipping {out}: {ultrahdr_app_heif} not built")
            return
        app = ultrahdr_app_heif

    sdr, boost = pattern(fmt, desc)
    pq = nits_to_pq(to_2020_nits(sdr, boost))

    base = os.path.join(tmpfolder, "base.rgba8888")
    hdr = os.path.join(tmpfolder, "hdr.rgba1010102")

    np.dstack([sdr, np.full(sdr.shape[:2], 255, np.uint8)]).tofile(base)

    # RGBA1010102: R in the low 10 bits, then G, then B, alpha in the top 2
    c = np.clip(pq * 1023 + 0.5, 0, 1023).astype(np.uint32)
    packed = c[..., 0] | (c[..., 1] << 10) | (c[..., 2] << 20) | (3 << 30)
    packed.astype("<u4").tofile(hdr)

    run(
        f"{q(app)} -m 0 -p {q(hdr)} -a 5 -y {q(base)} -b 3"
        f" -w {w} -h {w} -C 2 -t 2 -c 0 -R 1 -q 95 -Q 95 -z {q(out)}"
    )
    run(f"{q(app)} -m 1 -j {q(out)} -P")
    os.remove(base)
    os.remove(hdr)


def gainmap_libavif(fmt, desc, out):
    """ISO 21496-1 gain map AVIF, gain map computed by libavif from the pair."""
    sdr, boost = pattern(fmt, desc)
    pq = nits_to_pq(to_2020_nits(sdr, boost))

    base = os.path.join(tmpfolder, "base.png")
    alt = os.path.join(tmpfolder, "alternate.png")
    Image.fromarray(sdr).save(base)
    write_png16(alt, pq)

    run(
        f"{q(avifgainmaputil)} combine {q(base)} {q(alt)} {q(out)}"
        f" --cicp-alternate 9/16/9 -d 8 -y 444 -q 90 --qgain-map 90 -s 4"
    )
    run(f"{q(avifgainmaputil)} printmetadata {q(out)}")
    os.remove(base)
    os.remove(alt)


pq = partial(single_layer, transfer="pq")
hlg = partial(single_layer, transfer="hlg")

# yapf: disable
formats = [
    (gainmap,         "JPEG gain map", "UltraHDR, sRGB base + BT.2100 PQ", "jpg"),
    (gainmap,         "AVIF gain map", "UltraHDR, sRGB base + BT.2100 PQ", "avif"),
    (gainmap_libavif, "AVIF gain map", "ISO 21496-1, sRGB base + BT.2100 PQ", "avif"),
    (pq,              "AVIF PQ", "BT.2100 PQ, BT.2020, 10 bit, 4:4:4", "avif"),
    (hlg,             "AVIF HLG", "BT.2100 HLG, BT.2020, 10 bit, 4:4:4", "avif"),
    (pq,              "JXL PQ", "BT.2100 PQ, BT.2020, 16 bit", "jxl"),
    (hlg,             "JXL HLG", "BT.2100 HLG, BT.2020, 16 bit", "jxl"),
]
# yapf: enable

os.makedirs(tmpfolder, exist_ok=True)

for i, (encode, fmt, desc, ext) in enumerate(formats, 0):
    out = os.path.join(outfolder, f"{i:03d}.{ext}")
    print(f"{out}\t{fmt}\t{desc}")
    encode(fmt, desc, out)

os.rmdir(tmpfolder)
