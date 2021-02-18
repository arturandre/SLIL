# Street Level Imagery Labeler (SLIL)
## What is it?

The SLIL tool was created to help in the task
of manually labelling street level images into
the categories of images with:
- Trees
- Overhead power lines
- Intersections of power lines with trees

## How to install it?
It is based on python 3.6, but theoretically it
should work on any newer version.

So firstly you need to install the packages from
the requirements.txt by running for example:

`pip3 install -r requirements.txt`

Then you can run the code running:

`python3 slil.py`

## Ok, it runs, now what?

Well, you can load a folder using the menu:

1. <ins>F</ins>ile -> <ins>C</ins>hoose folder

then choose a folder containing images.

Notice that the summary file (by default summan.smr)
will be created (or read from) this folder. You can
also load a custom file by pressing:

2. <ins>F</ins>ile -> <ins>L</ins>oad labels


Then you can check the *checkboxes* corresponding
to classes present in the current image
(by defaul trees, power lines or the intersection of them)
and either press the yellow **Save** button, of if the
checkbox **Auto-save** is checked, you can also just
press the yellow **Next ->** button or its corresponding
keyboard key *right arrow ->*.

After labeling some images you need to commit the chages
back to the summary file by using the Save button:

3. 1. <ins>F</ins>ile -> S<ins>a</ins>ve labels

Or alternatively you can create another summary file elsewhere using:

3. 2. <ins>F</ins>ile -> <ins>S</ins>ave as labels


### And the other checkboxes and buttons?
- The yellow **<- Previous** button selects the previous
indexed image or the last in the list if the current one
is the first (image with the index 0).

- The **Only unlabeled** checkbox skips images that were
already labeled.

**Warning:** If you keep 'Auto-save' and 'Only unlabeled' both checked, and accidentally press the 'Next' or 'Previous' button will result in the current labels being saved and an attempt to come back to fix it will skip it because now that image is no longer unlabelled. If you need to come back to an already labeled image firstly you need to uncked the 'Only unlabeled' checkbox.

- The **Ignore exported** checkbox will skip images marked as exported.

- The menu **<inv>E</inv>xport** has the buttons:
- **<inv>E</inv>xport batch**: Used to create another summary file with a part (i.e. batch size) of the unlabelled images. This is usefull to allow multiple persons to simultaneously label the images, provided that each person has access to the partition that the exported summary file refers to.
- **<inv>M</inv>erge (import batch)**: After annotating the exported
summary file it can be merged back into the original summary using this
button. This will take the annotated entries from the exported file
and write their values over the corresponding entries in the current
opened summary file. Notice that entries already fulfilled in the
current summary file will be ignored. Furthermore, entries that
only exist in the exported file will also be ignored.

## Ok, but can I annotate other things?

Yes, you can! But be careful and avoid opening
a summary file that has different labels.

To change the labels showing in the application you can set
the variable **labels** in the file *summarymanager_config.txt*.
That is a comma-separated list, so you can change the current
labels, or insert new ones by appending a new label with a comma.
For example, you can add the label 'Car' after 'Intersetion'
by setting **labels** from

`labels = 'Tree,Pole w/ wire,Intersection'`

to

`labels = 'Tree,Pole w/ wire,Intersection,Cars'`.

