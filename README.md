Annotation Web
====================================

Annotation Web is a web-based annnotation system made primarily for easy annotation of 
image sequences such as ultrasound and camera recordings.
It uses mainly django/python for the backend and javascript/jQuery and HTML canvas for 
the interactive annotation frontend.

Annotation Web is developed by SINTEF Medical Technology and Norwegian University of Science and Technology (NTNU), and is released under a permissive [MIT license](https://github.com/smistad/annotationweb/blob/master/LICENSE.md).

You are more than welcome to contribute to this project, and feel free to ask questions.

![Annotation web](https://github.com/smistad/annotationweb/wiki/images/annotationweb.png)

### [Video presentation of Annotation Web on YouTube](https://www.youtube.com/watch?v=SzGJTVdVons)
Presentation of Annotation Web on IEEE IUS 2021.

### [Scientific article on Annotation Web](https://www.eriksmistad.no/wp-content/uploads/IUS_2021___Annotation_web.pdf)
Please cite this article if you use annotation web in your work.  
*Annotation Web-An open-source web-based annotation tool for ultrasound images  
Erik Smistad, Andreas Østvik, Lasse Løvstakken  
2021 IEEE International Ultrasonics Symposium (IUS)*

## Main features
* Pure web-based system. Annotaters only need a web browser, they don't have to install anything, and everything is stored on the server.
* Fast and interactive annotation of temporal data/video using javascript and HTML 5 canvas.
* Secure login with two-factor authentication.
* Multiple annotation tasks are implemented, such image classification, segmentation using splines, landmark and bounding box.

## Documentation
For more information, see the following wiki pages:
* [System overview](https://github.com/smistad/annotationweb/wiki/System-overview) - Overview of the system design, goal, code structure, etc.
* [Development setup](https://github.com/smistad/annotationweb/wiki/Development-setup) - Running annotation web locally on your machine
* [Server setup](https://github.com/smistad/annotationweb/wiki/Server-setup) - Running annotation web on a server
* [Importing data](https://github.com/smistad/annotationweb/wiki/Importing-data)
* [User management](https://github.com/smistad/annotationweb/wiki/User-management) - Create users, admins, change password, add 2FA for users ++
* [Setting up an annotation task](https://github.com/smistad/annotationweb/wiki/Setup-annotation-task)
* [Exporting annotated data](https://github.com/smistad/annotationweb/wiki/Export-annotations)

