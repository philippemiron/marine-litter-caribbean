ffmpeg -framerate 24 -pattern_type glob -i 'countries/cm_uniform_0_*.png' -vcodec libx264 -pix_fmt yuv420p -crf 20 antigua_and_barbuda.mp4
ffmpeg -framerate 24 -pattern_type glob -i 'countries/cm_uniform_10_*.png' -vcodec libx264 -pix_fmt yuv420p -crf 20 saint_lucia.mp4
ffmpeg -framerate 24 -pattern_type glob -i 'countries/cm_uniform_12_*.png' -vcodec libx264 -pix_fmt yuv420p -crf 20 trinidad_and_tobago.mp4
