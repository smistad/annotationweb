
function sendDataForSave() {
    return $.ajax({
        type: "POST",
        url: "/classification/save/",
        data: {
            image_id: g_imageID,
            task_id: g_taskID,
            label_id: g_currentLabel,
            quality: $('input[name=quality]:checked').val(),
            rejected: g_rejected ? 'true':'false',
            comments: $('#comments').val(),
            target_frames: JSON.stringify(g_targetFrames),
        },
        dataType: "json" // Need this do get result back as JSON
    });
}

function loadClassificationTask() {

    $('#clearButton').click(function() {
        g_annotationHasChanged = true;
        // Reset image quality form
        $('#imageQualityForm input[type="radio"]').each(function(){
            $(this).prop('checked', false);
        });
        // Set all label buttons to inactive
        changeLabel(-1);
    });

    // Add click listener for label buttons to trigger save
    for(var i = 0; i < g_labelButtons.length; ++i) {
        var label_id = g_labelButtons[i].id;
        $('#labelButton' + label_id).click(function() {
            // Only trigger save if label has no children
            var childrenFound = false;
            for(var j = 0; j < g_labelButtons.length; j++) {
                var child_label = g_labelButtons[j];
                if(child_label.parent_id == g_currentLabel) {
                    childrenFound = true;
                } else if(child_label.parent_id != 0) {
                }
            }
            if(!childrenFound)
                save();
        });
    }
}


function loadClassificationSequence(
    image_sequence_id, start_frame, nrOfFrames, show_entire_sequence,
    user_frame_selection, annotate_single_frame, frames_to_annotate,
    images_to_load_before, images_to_load_after, auto_play, classification_type
        ){
    /*
    This function overloads the loadSequence() function in annotationweb.js and
    is used for the classification tasks

    Changes
    -------
    - Introduce three types of classification that are set with the parameter
        `classification_type`. These are introduced below.
    - Subsequently remove the `annotate_single_frame` parameter since this is
        no longer relevant.
    - Adapt and redefine the parameter `user_frame_selection` to be suitable for
        each of the three types of classification tasks.

    Classification types
    --------------------
    (1) Single-frame classification: **Not implemented**
        The admin or the user themselves (if `user_frame_selection`is set)
        selects single keyframes to be annotated. Each of these keyframes
        receive an individual label.
        - `user_frame_selection`: Determines whether admin or user selects frames
        - `annotate_single_frame`: Irrelevant if `classification_type` introduced

    (2) Whole sequence classification:
        The whole sequence is classified with the same label. No keyframes are
        selected by admins or users. Instead, the last frame in the sequence is
        assigned as a keyframe to store the label for the sequence.
        For this type of classification, one should probably suggest to use
        `Reject` if the sequence contains multiple classes.
        - `user_frame_selection`: Irrelevant. Subsequences are selected by the user
        - `annotate_single_frame`: Irrelevant if `classification_type` introduced

    (3) Subsequence classification: **Not implemented**
        Subsequences (parts of a whole sequence) can be classified with
        different labels.
        - `user_frame_selection`: Irrelevant. Subsequences are selected by the user
        - `annotate_single_frame`: Irrelevant if `classification_type` introduced

     */

    console.log('Classification type chosen: ' + classification_type);
    console.log('User frame selection: ' + user_frame_selection);
    if (classification_type === 'single_frame') {
        if (!user_frame_selection && frames_to_annotate.length === 0) {
            // Admin set to select keyframes, but has selected none --> Give error message??
        } else {
            // frames_to_annotate will be used to set keyframes later in the function
        }

    } else if (classification_type === 'whole_sequence') {
        // Select last frame as target frame
        frames_to_annotate.push(nrOfFrames - 1);
        // user_frame_selection = false;
    } else if (classification_type === 'subsequence') {
        // User frame selection is irrelevant for whole-sequence classification
        // Currently not implemented, so should not have the option to choose this classification type
    } else {
        console.log('wrong classification type indicated');
    }


    // If user cannot select frame, and there are no target frames, select last frame as target frame
    // if (!user_frame_selection && annotate_single_frame && frames_to_annotate.length === 0) {
    //     // Select last frame as target frame
    //     frames_to_annotate.push(nrOfFrames - 1);
    // }
    g_userFrameSelection = user_frame_selection;

    // Check for ECG
    $.get('/ecg/' + image_sequence_id + '/', function (data, status) {
        if (data !== 'NO') {
            g_ecgData = data['ecg'];
            g_ecgMin = Number.MAX_VALUE;
            g_ecgMax = -Number.MAX_VALUE;
            for (let i = 0; i < g_ecgData.length; ++i) {
                if (g_ecgData[i]['value'] < g_ecgMin)
                    g_ecgMin = g_ecgData[i]['value'];
                if (g_ecgData[i]['value'] > g_ecgMax)
                    g_ecgMax = g_ecgData[i]['value'];
            }

            // Create ECG plot
            // Create canvas
            var sequenceDiv = document.getElementById('slider');
            var canvas = document.createElement('canvas');
            sequenceDiv.before(canvas);
            let canvasHeight = 100;
            canvas.setAttribute('width', $('#contentLeft').width());
            canvas.setAttribute('height', canvasHeight);
            canvas.setAttribute('id', 'ecgCanvas');
            canvas.setAttribute('style', 'width: 100%; height: ' + canvasHeight + 'px;');
            // IE stuff
            if (typeof G_vmlCanvasManager != 'undefined') {
                canvas = G_vmlCanvasManager.initElement(canvas);
            }
            g_ecgContext = canvas.getContext("2d");

            drawECG();
        }
    });

    console.log('In load sequence');
    // Create play/pause button
    setPlayButton(auto_play);
    $("#playButton").click(function () {
        setPlayButton(!g_isPlaying);
        if (g_isPlaying) // Start it again
            incrementFrame();
    });

    // Create canvas
    var canvas = document.getElementById('canvas');
    canvas.setAttribute('width', g_canvasWidth);
    canvas.setAttribute('height', g_canvasHeight);
    // IE stuff
    if (typeof G_vmlCanvasManager != 'undefined') {
        canvas = G_vmlCanvasManager.initElement(canvas);
    }
    g_context = canvas.getContext("2d");

    if (g_targetFrames.length > 0) {
        g_currentFrameNr = g_targetFrames[0];
    } else {
        g_currentFrameNr = 0;
    }

    var start;
    var end;
    var totalToLoad;
    if (show_entire_sequence || !annotate_single_frame) {
        start = start_frame;
        end = start_frame + nrOfFrames - 1;
        totalToLoad = nrOfFrames;
    } else {
        start = max(start_frame, g_currentFrameNr - images_to_load_before);
        end = min(start_frame + nrOfFrames - 1, g_currentFrameNr + images_to_load_after);
        totalToLoad = end - start;
    }
    g_startFrame = start;
    g_sequenceLength = end - start;

    // Create slider
    $("#slider").slider(
        {
            range: "max",
            min: start,
            max: end,
            step: 1,
            value: g_currentFrameNr,
            slide: function (event, ui) {
                goToFrame(ui.value);
            }
        }
    );

    // Create progress bar
    g_progressbar = $("#progressbar");
    var progressLabel = $(".progress-label");
    g_progressbar.progressbar({
        value: false,
        change: function () {
            progressLabel.text("Please wait while loading. " + g_progressbar.progressbar("value").toFixed(1) + "%");
        },
        complete: function () {
            // Remove progress bar and redraw
            progressLabel.text("Finished loading!");
            g_progressbar.hide();
            redrawSequence();
            g_progressbar.trigger('markercomplete');
            if (g_isPlaying)
                incrementFrame();
        }
    });

    for (var i = 0; i < frames_to_annotate.length; ++i) {
        addKeyFrame(frames_to_annotate[i]);
        if (classification_type === 'whole_sequence') {
            // don't show slider mark
            $('#sliderMarker' + frames_to_annotate[i]).remove();
        }
    }


    $("#addFrameButton").click(function () {
        setPlayButton(false);
        addKeyFrame(g_currentFrameNr);
        g_currentTargetFrameIndex = g_targetFrames.length - 1;
    });

    $("#removeFrameButton").click(function () {
        setPlayButton(false);
        if (g_targetFrames.includes(g_currentFrameNr)) {
            g_targetFrames.splice(g_targetFrames.indexOf(g_currentFrameNr), 1);
            g_currentTargetFrameIndex = -1;
            $('#sliderMarker' + g_currentFrameNr).remove();
            $('#selectedFrames' + g_currentFrameNr).remove();
            $('#selectedFramesForm' + g_currentFrameNr).remove();
        }
    });

    $("#nextFrameButton").click(function () {
        goToNextKeyFrame();
    });

    // Moving between frames
    // Scrolling (mouse must be over canvas)
    $("#canvas").bind('mousewheel DOMMouseScroll', function (event) {
        g_shiftKeyPressed = event.shiftKey;
        console.log('Mousewheel event!');
        if (event.originalEvent.wheelDelta > 0 || event.originalEvent.detail < 0) {
            // scroll up
            if (g_shiftKeyPressed) {
                goToNextKeyFrame();
            } else {
                goToFrame(g_currentFrameNr + 1);
            }
        } else {
            // scroll down
            if (g_shiftKeyPressed) {
                goToPreviousKeyFrame();
            } else {
                goToFrame(g_currentFrameNr - 1);
            }
        }
        event.preventDefault();
    });

    $(document).keydown(function (e) {
        console.log(String.fromCharCode(e.which));
        if (String.fromCharCode(e.which) == 'Z') {
            g_zoom = true;
        }
    });
    $(document).keyup(function (e) {
        console.log('up', String.fromCharCode(e.which));
        if (String.fromCharCode(e.which) == 'Z') {
            g_zoom = false;
        }
    });

    $('#canvas').mousemove(function (e) {
        var scale = g_canvasWidth / $('#canvas').width();
        var mouseX = (e.pageX - this.offsetLeft) * scale;
        var mouseY = (e.pageY - this.offsetTop) * scale;

        g_mousePositionX = mouseX;
        g_mousePositionY = mouseY;
    });

    // Arrow key pressed
    $(document).keydown(function (event) {
        g_shiftKeyPressed = event.shiftKey;
        if (event.which === 37) { // Left
            if (g_shiftKeyPressed) {
                goToPreviousKeyFrame();
            } else {
                goToFrame(g_currentFrameNr - 1);
            }
        } else if (event.which === 39) { // Right
            if (g_shiftKeyPressed) {
                goToNextKeyFrame();
            } else {
                goToFrame(g_currentFrameNr + 1);
            }
        } else if (event.which === 32) { // Space
            if ($("textarea").is(":focus")) {
                // Input and text area has focus, do nothing
            } else {
                setPlayButton(!g_isPlaying);
                incrementFrame();
                event.preventDefault();
            }
        }
    });

    $(document).keyup(function (event) {
        g_shiftKeyPressed = event.shiftKey;
    });


    // Load images
    g_framesLoaded = 0;
    //console.log('start: ' + start + ' end: ' + end)
    //console.log('target_frame: ' + target_frame)
    for (var i = start; i <= end; i++) {
        var image = new Image();
        image.src = '/show_frame/' + image_sequence_id + '/' + i + '/' + g_taskID + '/';
        image.onload = function () {
            g_canvasWidth = this.width;
            g_canvasHeight = this.height;
            canvas.setAttribute('width', g_canvasWidth);
            canvas.setAttribute('height', g_canvasHeight);

            // Update progressbar
            g_framesLoaded++;
            g_progressbar.progressbar("value", g_framesLoaded * 100 / totalToLoad);
        };
        g_sequence.push(image);
    }
}
