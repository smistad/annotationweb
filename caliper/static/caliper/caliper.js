var g_backgroundImage;
var g_currentColor = null;
var g_controlPoints = {}; // control point dictionary [key_frame_nr] contains a dictionary/map of objects with a dictionary with label: label data, control_points: list
var g_currentObject = 0; // Which index in g_controlPoints[key_frame_nr] list we are in
var g_move = false;
var g_pointToMove = -1;
var g_labelToMove = -1;
var g_moveDistanceThreshold = 8;
var g_drawLine = false;
var g_currentLabel = -1;
let g_spacingX = 1;
let g_spacingY = 1;

function getMaxObjectID() {
    var max = -1;
    for(var key in g_controlPoints[g_currentFrameNr]) {
        key = parseInt(key); // dictionary keys are strings
        if(key > max)
            max = key;
    }
    return max;
}

function setup() {

    // Define event callbacks
    $('#canvas').mousedown(function(e) {
        if(e.ctrlKey && g_controlPoints[g_currentFrameNr][g_currentObject].control_points.length >= 2) { // Create new object if ctrl key is held down AND current object has more than 1 points
            g_currentObject = getMaxObjectID()+1;
            data = {label: g_labelButtons[g_currentLabel], control_points: []};
            g_controlPoints[g_currentFrameNr][g_currentObject] = data;
        }

        const pos = getMousePos(e) ;
        var point = getClosestPoint(pos.x, pos.y);
        if(point !== false) {
            // Activate object of this point
            g_currentObject = point.object;
            $('.labelButton').removeClass('activeLabel');
            $('#labelButton' + point.label_idx).addClass('activeLabel');
            g_currentLabel = getLabelIdxWithId(point.label_idx);
            // Move point
            g_move = true;
            g_pointToMove = point.index;
            g_labelToMove = point.label_idx;
        } else {
            var section = isPointOnLine(pos.x, pos.y);
            if(section >= 0) {
                // Insert point
                insertControlPoint(pos.x, pos.y, g_labelButtons[g_currentLabel].id, section);
            } else if(g_isPlaying === false) {
                addControlPointsForNewFrame(g_currentFrameNr);
                // Add point at end
                addControlPoint(pos.x, pos.y, g_currentFrameNr, g_currentObject, g_labelButtons[g_currentLabel].id, g_shiftKeyPressed);
            }
        }
        redrawSequence();
    });

    $('#canvas').mousemove(function(e) {
        const pos = getMousePos(e) ;
        var cursor = 'default';

        if(g_move) {
            cursor = 'move';
            setControlPoint(g_pointToMove, g_currentObject, pos.x, pos.y);
            redrawSequence();
        } else {
            if(!e.ctrlKey &&
                g_currentFrameNr in g_controlPoints &&
                g_currentObject in g_controlPoints[g_currentFrameNr] &&
                g_controlPoints[g_currentFrameNr][g_currentObject].control_points.length > 0 &&
                isPointOnLine(pos.x, pos.y) < 0) {
                // If mouse is not close to line, draw dotted drawing line
                var line = {
                    x0: getControlPoint(-1, g_currentObject).x,
                    y0: getControlPoint(-1, g_currentObject).y,
                    x1: pos.x,
                    y1: pos.y
                };
                g_drawLine = line;
            } else {
                cursor = 'pointer';
                g_drawLine = false;
            }
            redrawSequence();
        }
        $('#canvas').css({'cursor' : cursor});
        e.preventDefault();
    });

    $('#canvas').mouseup(function(e) {
        g_move = false;
    });

    $('#canvas').mouseleave(function(e) {
        g_drawLine = false;
        redrawSequence();
    });

    $('#canvas').dblclick(function(e) {
        if(g_move)
            return;
        const pos = getMousePos(e) ;
        var point = getClosestPoint(pos.x, pos.y);
        if(point !== false) {
            g_controlPoints[g_currentFrameNr][g_currentObject].control_points.splice(point.index, 1);
            //if(g_controlPoints[g_currentFrameNr[g_currentObject]].control_points.length == 0) {
            //    g_controlPoints[g_currentFrameNr].splice(g_currentObject, 1); // remove this object
            //}
        }
        redrawSequence();
    });


    $("#clearButton").click(function() {
        g_annotationHasChanged = true;
        g_controlPoints[g_currentFrameNr][g_currentObject].control_points = [];
        redrawSequence();
    });

    $('#removeFrameButton').click(function() {
        // Remove lines in this frame
        if(g_currentFrameNr in g_controlPoints){
            delete g_controlPoints[g_currentFrameNr];
        }
        redrawSequence();
    });

    $(document).keydown(function(event) {
       if(event.ctrlKey)  {
           g_drawLine = false;
           redrawSequence();
       }
    });

    $('#addFrameButton').click(function() {
        addControlPointsForNewFrame(g_currentFrameNr);
    });

    // Set first label active
    changeLabel(g_labelButtons[0].id)

    redraw();

}

function addControlPointsForNewFrame(frameNr) {
    if(frameNr in g_controlPoints) // Already exists
        return;
    g_controlPoints[frameNr] = {};
    addKeyFrame(frameNr);
}

function loadSegmentationTask(image_sequence_id) {
    getImageFrame(image_sequence_id, 0, g_taskID).then(image => {
        g_canvasWidth = image.width;
        g_canvasHeight = image.height;
        g_backgroundImage = image;
        $.get('/image-spacing/' + image_sequence_id + '/', function(data, status, xhr) {
            if(xhr.status === 200) {
                let parts = data.split(';')
                //g_spacingX = parseFloat(parts[0]);
                g_spacingY = parseFloat(parts[1]);
                g_spacingX = g_spacingY; // Image is made isotropic before sent, see common/utility.py:get_image_as_http_response
            }
        }).done(function() {
            setup();
        });
    });
}

function getClosestPoint(x, y) {
    var minDistance = g_canvasWidth*g_canvasHeight;
    var minPoint = -1;
    var minLabel = -1;
    var minObject = -1;

    for(var j in g_controlPoints[g_currentFrameNr]) {
        for(var i = 0; i < g_controlPoints[g_currentFrameNr][j].control_points.length; i++) {
            var point = getControlPoint(i, j);
            var distance = Math.sqrt((point.x - x) * (point.x - x) + (point.y - y) * (point.y - y));
            if(distance < minDistance) {
                minPoint = i;
                minDistance = distance;
                minLabel = g_controlPoints[g_currentFrameNr][j].label.id;
                minObject = j;
            }
        }
    }

    if(minDistance < g_moveDistanceThreshold) {
        return {index: minPoint, label_idx: minLabel, object: minObject};
    } else {
        return false;
    }
}

function createControlPoint(x, y, label, uncertain) {
    // Find label index
    var labelIndex = 0;
    for(var i = 0; i < g_labelButtons.length; i++) {
        if(g_labelButtons[i].id == label) {
            labelIndex = i;
            break;
        }
    }

    var controlPoint = {
        x: x,
        y: y,
        label_id: label, // actual DB id
        label: labelIndex, // index: only used for color
        uncertain: uncertain    // whether the user is uncertain about this point or not
    };
    return controlPoint;
}

function insertControlPoint(x, y, label, index) {
    var controlPoint = createControlPoint(x, y, label, g_shiftKeyPressed);
    g_controlPoints[g_currentFrameNr][g_currentObject].control_points.splice(index+1, 0, controlPoint);
}

function addControlPoint(x, y, target_frame, object, label, uncertain) {
    var controlPoint = createControlPoint(x, y, label, uncertain);
    if(!(object in g_controlPoints[target_frame])) // add object if it doesn't exist
        g_controlPoints[target_frame][object] = {label: g_labelButtons[getLabelIdxWithId(label)], control_points: []};
    g_controlPoints[target_frame][object].control_points.push(controlPoint);
}

function getControlPoint(index, object) {
    if(index === -1) {
        index = g_controlPoints[g_currentFrameNr][object].control_points.length-1;
    }
    return g_controlPoints[g_currentFrameNr][object].control_points[index];
}

function setControlPoint(index, object, x, y) {
    g_controlPoints[g_currentFrameNr][object].control_points[index].x = x;
    g_controlPoints[g_currentFrameNr][object].control_points[index].y = y;
}

function isPointOnLine(pointX, pointY) {
    for(var object in g_controlPoints[g_currentFrameNr]) {
        for (var i = 0; i < g_controlPoints[g_currentFrameNr][object].control_points.length-1; ++i) {
            var a = g_controlPoints[g_currentFrameNr][object].control_points[i];
            var b = g_controlPoints[g_currentFrameNr][object].control_points[i+1];

            let distance = Math.sqrt((a.x-b.x)*(a.x-b.x) + (a.y-b.y)*(a.y-b.y))
            let directionX = (b.x - a.x) / distance;
            let directionY = (b.y - a.y) / distance;


            for (let t = 0.0; t < distance; t += 0.5) {
                let x = a.x + directionX*t;
                let y = a.y + directionY*t;

                if (Math.sqrt((pointX - x) * (pointX - x) + (pointY - y) * (pointY - y)) < g_moveDistanceThreshold) {
                    return i;
                }
            }
        }
    }
    return -1;
}

function redraw(){
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);

    if(!(g_currentFrameNr in g_controlPoints))
        return;

    var controlPointSize = 6;
    g_context.lineWidth = 2;

    // Draw controlPoint
    for(var j in g_controlPoints[g_currentFrameNr]) {
        var label = g_controlPoints[g_currentFrameNr][j].label;
        for(var i = 0; i < g_controlPoints[g_currentFrameNr][j].control_points.length; i++) {
            g_context.beginPath();
            g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);

            let point0 = g_controlPoints[g_currentFrameNr][j].control_points[i]
            // Draw line to next point if it exists
            if(i+1 < g_controlPoints[g_currentFrameNr][j].control_points.length) {
                g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
                g_context.moveTo(point0.x, point0.y);
                let point1 = g_controlPoints[g_currentFrameNr][j].control_points[i+1]
                let distance = Math.sqrt((point1.x-point0.x)*(point1.x-point0.x)*g_spacingX*g_spacingX + (point1.y-point0.y)*(point1.y-point0.y)*g_spacingY*g_spacingY);
                g_context.lineTo(point1.x, point1.y);
                g_context.stroke();
                g_context.font = '16px bold';
                g_context.fillStyle = 'yellow';
                g_context.fillText(distance.toFixed(1), point0.x + (point1.x-point0.x)/2.0 + 4, point0.y + (point1.y-point0.y)/2.0 + 8);
            }

            // Draw control point
            g_context.fillStyle = colorToHexString(255, 255, 0);
            g_context.fillRect(point0.x - controlPointSize / 2, point0.y - controlPointSize / 2, controlPointSize, controlPointSize);
        }
    }

    if(g_drawLine !== false) {
        g_context.beginPath();
        g_context.setLineDash([5, 5]); // dashes are 5px and spaces are 5px
        var label = g_labelButtons[g_currentLabel];
        g_context.strokeStyle = colorToHexString(label.red, label.green, label.blue);
        g_context.moveTo(g_drawLine.x0, g_drawLine.y0);
        g_context.lineTo(g_drawLine.x1, g_drawLine.y1);
        g_context.stroke();
        g_context.setLineDash([]); // Clear
    }
}

// Override redraw sequence in sequence.js
function redrawSequence() {
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight);
    redraw();
    if(g_zoom) {
        // Zoom at mouse position when moving control points
        zoomAtMousePosition(g_mousePositionX, g_mousePositionY);
    }
}

function getLabelIdxWithId(id) {
    for(var i = 0; i < g_labelButtons.length; i++) {
        if(g_labelButtons[i].id == id) {
            return i;
        }
    }
}

// Override of annotationweb.js
function changeLabel(label_id) {
    console.log('changing label to: ', label_id)
    $('.labelButton').removeClass('activeLabel');
    $('#labelButton' + label_id).addClass('activeLabel');
    g_currentLabel = getLabelIdxWithId(label_id);

    // changeLabel is called when we press the label button (may or may not have an object),
    // and when we press a control point (already have object)
    if(g_currentFrameNr in g_controlPoints) {
        var found = false;
        for(var j in g_controlPoints[g_currentFrameNr]) {
            if(g_controlPoints[g_currentFrameNr][j].label.id == label_id) {
                g_currentObject = j;
                found = true;
                break;
            }
        }
        if(!found) {
            // Create new object id
            g_currentObject = getMaxObjectID()+1;
            g_controlPoints[g_currentFrameNr][g_currentObject] = {label: g_labelButtons[getLabelIdxWithId(label)], control_points: []};
        }
    }
}

function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/caliper/save/",
        data: {
            control_points: JSON.stringify(g_controlPoints),
            target_frames: JSON.stringify(g_targetFrames),
            n_labels: g_labelButtons.length,
            width: g_canvasWidth,
            height: g_canvasHeight,
            image_id: g_imageID,
            task_id: g_taskID,
            rejected: g_rejected ? 'true':'false',
            comments: $('#comments').val(),
            quality: $('input[name=quality]:checked').val(),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}
