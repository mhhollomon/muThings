#!/usr/bin/env bash

echo "---------- boxes"
./mupic ./tests/boxes.mupic

echo "---------- image_fits"
./mupic ./tests/image_fits.mupic

echo "---------- land-cover-one-border"
./mupic ./tests/land-cover-one-border.mupic

echo "---------- land-cover-square"
./mupic ./tests/land-cover-square.mupic

echo "---------- margins"
./mupic ./tests/margins.mupic

echo "---------- maxsquare"
./mupic ./tests/maxsquare.mupic

echo "---------- new_borders"
./mupic ./tests/new_borders.mupic

echo "---------- offsets"
./mupic ./tests/offsets.mupic

echo "---------- templates"
./mupic ./tests/templates.mupic

echo "---------- zorder"
./mupic ./tests/zorder.mupic
