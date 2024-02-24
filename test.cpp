#include <cstdio>

#include "jpeglib.h"
#include <fstream>
#include <iostream>
#include <lcms2.h>
#include <memory>
#include <png.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <vector>

int main() {
  jpeg_decompress_struct jinfo = jpeg_decompress_struct{};
  auto jerr = jpeg_error_mgr{};

  jinfo.err = jpeg_std_error(&jerr);
  jerr.error_exit = [](j_common_ptr info) {
    char jpegLastErrorMsg[JMSG_LENGTH_MAX];
    (*(info->err->format_message))(info, jpegLastErrorMsg);
    throw std::runtime_error(jpegLastErrorMsg);
  };
  jpeg_create_decompress(&jinfo);

  printf("reading\n");
  // std::ifstream infile("images/JPEG.CMYK no ICC.jpg");
  std::ifstream infile("images/JPEG.L.jpg");

  infile.seekg(0, std::ios::end);
  size_t size = infile.tellg();
  infile.seekg(0, std::ios::beg);

  std::vector<uint8_t> bytes;
  bytes.reserve(size);

  infile.read(reinterpret_cast<char *>(bytes.data()), size);

  jpeg_mem_src(&jinfo, bytes.data(), size);
  jpeg_save_markers(&jinfo, JPEG_APP0 + 2, 0xFFFF);
  jpeg_read_header(&jinfo, true);

  printf("size %d %d\n", jinfo.image_width, jinfo.image_height);
  printf("cmyk %d\n", jinfo.jpeg_color_space == JCS_CMYK);

  jinfo.out_color_space = JCS_GRAYSCALE;

  // std::ifstream iccfile("USWebCoatedSWOP.icc");
  std::ifstream iccfile("ISOcoated_v2_grey1c_bas.ICC");

  iccfile.seekg(0, std::ios::end);
  size_t iccsize = iccfile.tellg();
  iccfile.seekg(0, std::ios::beg);

  std::vector<uint8_t> iccbytes;
  iccbytes.reserve(iccsize);

  iccfile.read(reinterpret_cast<char *>(iccbytes.data()), iccsize);

  auto icc1 = cmsOpenProfileFromMem(iccbytes.data(), iccsize);

  // icc1 = cmsCreate_sRGBProfile();
  auto icc2 = cmsCreate_sRGBProfile();

  // auto transform = cmsCreateTransform(icc1, TYPE_CMYK_8_REV, icc2,
  // TYPE_RGBA_8,
  auto transform = cmsCreateTransform(icc1, TYPE_GRAY_8, icc2, TYPE_RGBA_8,
                                      cmsGetHeaderRenderingIntent(icc1), 0);

  cmsCloseProfile(icc1);
  cmsCloseProfile(icc2);

  std::vector<uint8_t> image;
  image.resize(jinfo.image_width * jinfo.image_height * 4);
  uint8_t *pimage = image.data();

  uint8_t stride = jinfo.image_width * 4;
  printf("decoding\n");

  printf("inverted %d\n", jinfo.saw_Adobe_marker);

  std::vector<uint8_t> cmsline(jinfo.image_width * 4);
  uint8_t *pline = cmsline.data();

  jpeg_start_decompress(&jinfo);

  int y = 0;
  while (jinfo.output_scanline < jinfo.output_height) {
    uint8_t *out = pimage + y * jinfo.image_width * 4;

    jpeg_read_scanlines(&jinfo, &pline, 1);
    cmsDoTransform(transform, pline, out, jinfo.image_width);

    for (int i = 0; i < jinfo.image_width; i++) {
      out[i * 4 + 3] = 255;
    }
    y++;
  }

  FILE *fp = fopen("out.png", "wb");
  if (!fp)
    abort();

  png_structp png =
      png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
  if (!png)
    abort();

  png_infop info = png_create_info_struct(png);
  if (!info)
    abort();

  if (setjmp(png_jmpbuf(png)))
    abort();

  png_init_io(png, fp);

  png_set_IHDR(png, info, jinfo.image_width, jinfo.image_height, 8,
               PNG_COLOR_TYPE_RGB_ALPHA, PNG_INTERLACE_NONE,
               PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
  png_write_info(png, info);

  png_bytep *row_pointers =
      (png_bytep *)malloc(sizeof(png_bytep) * jinfo.image_height);

  for (uint32_t i = 0; i < jinfo.image_height; i++) {
    row_pointers[i] = (png_byte *)(pimage + jinfo.image_width * 4 * i);
  }

  png_write_image(png, row_pointers);
  png_write_end(png, NULL);

  fclose(fp);

  png_destroy_write_struct(&png, &info);

  return 0;
}
