Annotation web
====================================

Annotation web is a web-based annnotation system made primarily for easy annotation of 
image sequences such as ultrasound and camera recordings.
It uses mainly django/python for the backend and javascript/jQuery and HTML canvas for 
the interactive annotation frontend.

Annotation web is developed by SINTEF Medical Technology and Norwegian University of Science and Technology (NTNU), and is released under a permissive [MIT license](https://github.com/smistad/annotationweb/LICENSE.md)

You are more than welcome to contribute to this project, and feel free to ask questions.

Main features
* Pure web-based system. Annotaters only need a web browser, they don't have to install anything, and everything is stored on the server.
* Fast and interactive annotation of temporal data/video using javascript and HTML 5 canvas.
* Secure login with two-factor authentication
* Multiple annotation tasks are implemented, such image classification, segmentation using splines, landmark and bounding box.

For more information, see the following wiki pages:
* [Development setup](https://github.com/smistad/annotationweb/wiki/Development-setup) - Running annotation web locally on your machine
* [Server setup](https://github.com/smistad/annotationweb/wiki/Server-setup) - Running annotation web on a server
* [Importing data]()
* [Setting up an annotation task]()
* [Exporting annotated data]()
