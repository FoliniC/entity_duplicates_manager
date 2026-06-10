######################
#     HOW TO USE     #
######################
#
# Summary:
#   This script helps to create folders and move/rename a set of existing PNG images into those folders.
#   The script does not generate any images (this needs to be done by graphics staff from vector images in a sketch file) prior to running
#   this script.
#
# Details: 
#
#   The graphics/design staff can export a series of PNG files from a vector image, and while they are exporting, configure a custom naming
#   format and sizes which will export a separate PNG image to each scaled size. Graphics will then end up giving you a list of images all
#   in one folder. Problem is, each of these images need to be placed into their own subfolder and renamed before they can be imported into
#   the solution, which is manual work that can be automated.
#
#   By executing this script, you can save yourself some time by automating the creation of the folders (one folder for each scaled value)
#   and automate moving each image file into the relevant folder, as well as renaming each image to the correct final filename, ready to
#   import into the project.
#
#   To get this to work, graphics must provide images with the following naming convention configured from inside sketch before exporting:
#      <final filename>@<scaling factor as a number>.png
#
#   For example:
#      \Contact@100.png
#      \Contact@120.png
#      \Contact@125.png
#      etc.
#
#   The above example will then be converted to:
#      \scale-100\Contact.png
#      \scale-120\Contact.png
#      \scale-125\Contact.png
#      etc.
#
#   NOTE: If you're interested in additional reading on how Visual Studio handles these image directories see:
#      https://docs.microsoft.com/en-us/windows/uwp/app-resources/images-tailored-for-scale-theme-contrast
#      https://docs.microsoft.com/en-us/windows/uwp/app-resources/tailor-resources-lang-scale-contrast
#
#
# Instructions:
#
#   To execute this script:
#    1. Copy this script into the same folder as all of the PNG files
#    2. Execute the script in a unix terminal (if you're using Windows, open the Script with Git Bash which should already be installed as part
#       of your development environment)
#    3. Script should create all the relevant subfolders and move the images into them
#    4. Delete the copy of the script you created in step 1
#


###################
#     SCRIPT      #
###################

#!/bin/bash
for f in *.png;
do
    new_f=$(echo $f | sed s/@[0-9]*//); ## this creates a new file name by removing the pattern
    dir=$(echo $f | grep -Po "\d*"); ## this gets the dir name by getting only the pattern
    mkdir -p scale-"$dir" && mv "$f" "scale-$dir/$new_f"; ## this moves and renames the old file to the folder, also creates dir if it didn't exist
done