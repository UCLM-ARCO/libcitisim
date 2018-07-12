Overview
========

Python library for Citisim, to ease access for publishing and
subscribing to the different topics.

For more information:

* [Windows setup for libcitisim, using Python](http://pike.esi.uclm.es:8012/recipe/libcitisim_and_python_on_windows/)
* [Publishing events using libcitisim](http://pike.esi.uclm.es:8012/recipe/libcitisim_publishing_events/)
* [Subscribing for events using libcitisim](http://pike.esi.uclm.es:8012/recipe/libcitisim_topic_subscription/)

Installation of the library from repository
===========================================

In the root of the repo, execute the command:

$ python3 setup.py sdist

This command generates, inside folder dist, a source distribution (e.g. libcitisim-0.20180605.tar.gz) that can be installed with tools like pip:

$ pip3 install dist/libcitisim-0.20180605.tar.gz
.
.
Successfully installed libcitisim-0.20180605

