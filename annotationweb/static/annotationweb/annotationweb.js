var g_context;
var g_canvasWidth = 512;
var g_canvasHeight = 512;
var g_sequence = [];
var g_labelButtons = [];
var g_currentFrameNr; // The frame nr currently displayed
var g_startFrame;
var g_progressbar;
var g_framesLoaded;
var g_sequenceLength;
var g_isPlaying = true;
var g_returnURL = '';
var g_taskID;
var g_imageID;
var g_currentLabel = -1;
// Set this true if user has changed annotation. This will trigger a dialog
// if user press next or previous
var g_annotationHasChanged = false;
var g_nextURL = '';
var g_rejected = false;
var g_targetFrames = []; // Frames to annotate
var g_currentTargetFrameIndex = -1; // Index of current target frame (g_targetFrames), -1 if not on target frame
var g_shiftKeyPressed = false;
var g_userFrameSelection = false;

function max(a, b) {
    return a > b ? a : b;
}

function min(a, b) {
    return a < b ? a : b;
}

function mousePos(e, canvas) {
    var scale =  g_canvasWidth / $('#canvas').width();
    var mouseX = (e.pageX - canvas.offsetLeft)*scale;
    var mouseY = (e.pageY - canvas.offsetTop)*scale;
    return {
        x: mouseX,
        y: mouseY,
    }
}

function incrementFrame() {
    if(!g_isPlaying) // If this is set to false, stop playing
        return;
    g_currentFrameNr = ((g_currentFrameNr-g_startFrame) + 1) % g_framesLoaded + g_startFrame;
    var marker_index = g_targetFrames.findIndex(index => index === g_currentFrameNr);
    if(marker_index) {
        g_currentTargetFrameIndex = g_currentFrameNr;
    } else {
        g_currentTargetFrameIndex = -1;
    }
    $('#slider').slider('value', g_currentFrameNr); // Update slider
    $('#currentFrame').text(g_currentFrameNr);
    redrawSequence();
    window.setTimeout(incrementFrame, 100);
}

function setPlayButton(play) {
    g_isPlaying = play;
    if(g_isPlaying) {
        document.getElementById('playButton').title = 'Pause';
        document.getElementById('play').className = "fa fa-pause";
    } else {
        document.getElementById('playButton').title = 'Play';
        document.getElementById('play').className = "fa fa-play";
    }
}

function goToFrame(frameNr) {
    setPlayButton(false);
    g_currentFrameNr = min(max(0, frameNr), g_framesLoaded-1);
    $('#slider').slider('value', frameNr); // Update slider
    $('#currentFrame').text(g_currentFrameNr);
    var marker_index = g_targetFrames.findIndex(index => index === frameNr);
    if(marker_index) {
        g_currentTargetFrameIndex = g_currentFrameNr;
    } else {
        g_currentTargetFrameIndex = -1;
    }
    redrawSequence();
}

function save() {
    var messageBox = document.getElementById("message");
    messageBox.innerHTML = '<span class="info">Please wait while saving..</span>';
    sendDataForSave().done(function(data) {
        console.log("Save done..");
        console.log(data);
        var messageBox = document.getElementById("message");
        if(data.success == "true") {
            messageBox.innerHTML = '<span class="success">Image was saved</span>';
            if(g_returnURL != '') {
                window.location = g_returnURL;
            } else {
                // Reset image quality form before refreshing
                //$('#imageQualityForm')[0].reset();
                //$('#comments').val('');
                // Refresh page
                location.reload();
            }
        } else {
            messageBox.innerHTML = '<div class="error"><strong>Save failed</strong><br> ' + data.message + '</div>';
        }
        console.log(data.message);
    }).fail(function(data) {
        console.log("Ajax failed");
        var messageBox = document.getElementById("message");
        messageBox.innerHTML = '<span class="error">Save failed: remember to choose image quality</span>';
    }).always(function(data) {
        console.log("Ajax complete");
    });
    console.log("Save function executed");
}

function initializeAnnotation(taskID, imageID) {
    g_taskID = taskID;
    g_imageID = imageID;

    // This is required due to djangos CSRF protection
    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // Setup save button
    $('#saveButton').click(save);

    // If reject is selected, mark as rejected, then save
    $('#rejectButton').click(function() {
        g_rejected = true;
        save();
    });

    $('#imageQualityForm input[type="radio"]').change(function(){
        g_annotationHasChanged = true;
    });

    // Create dialog
    $("#dialogConfirm").dialog({
          resizable: false,
          height: "auto",
          width: 400,
          modal: true,
            autoOpen: false,
          buttons: {
            "Save and go to next/previous": function() {
              $( this ).dialog( "close" );
                g_returnURL = g_nextURL;
                save();
            },
            "Discard changes and go to next/previous": function() {
              $( this ).dialog( "close" );
                window.location.href = g_nextURL;
            },
            Cancel: function() {
              $( this ).dialog( "close" );
            },
          }
        });
}

function setupSliderMark(frame, color) {
    color = typeof color !== 'undefined' ? color : '#0077b3';

    var slider = document.getElementById('slider')

    var newMarker = document.createElement('span');
    newMarker.setAttribute('id', 'sliderMarker' + frame);
    $(newMarker).css('background-color', color);
    $(newMarker).css('width', $('.ui-slider-handle').css('width'));
    $(newMarker).css('margin-left', $('.ui-slider-handle').css('margin-left'));
    $(newMarker).css('height', '100%');
    $(newMarker).css('z-index', '99');
    $(newMarker).css('position', 'absolute');
    $(newMarker).css('left', ''+(100.0*(frame-g_startFrame)/g_sequenceLength)+'%');

    slider.appendChild(newMarker)
    console.log('Made marker');
}

function addKeyFrame(frame_nr, color) {
    color = typeof color !== 'undefined' ? color : '#0077b3';
    if(g_targetFrames.includes(frame_nr)) // Already exists
        return;
    setupSliderMark(frame_nr, color);
    g_targetFrames.push(frame_nr);
    g_targetFrames.sort(function(a, b){return a-b});
    $("#framesSelected").append('<li id="selectedFrames' + frame_nr + '">' + frame_nr + '</li>');
    $("#framesForm").append('<input id="selectedFramesForm' + frame_nr + '" type="hidden" name="frames" value="' + frame_nr + '">');
}

function goToNextKeyFrame() {
    if(g_targetFrames.length === 0)
        return;
    // Find next key frame
    let i;
    if(g_targetFrames[g_targetFrames.length-1] <= g_currentFrameNr) {
        i = 0;
    } else if(g_targetFrames.length === 1) {
        i = 0;
    } else {
        for (i = 0; i < g_targetFrames.length; i++) {
            if(g_targetFrames[i] > g_currentFrameNr)
                break;
        }
    }
    g_currentTargetFrameIndex = i;
    goToFrame(g_targetFrames[i]);
}

function goToPreviousKeyFrame() {
    if(g_targetFrames.length === 0)
        return;
    // Find previous key frame
    let i;
    if(g_targetFrames[0] >= g_currentFrameNr || g_targetFrames[g_targetFrames.length-1] < g_currentFrameNr) {
        i = g_targetFrames.length-1;
    } else if(g_targetFrames.length === 1) {
        i = 0;
    } else {
        for (i = g_targetFrames.length-1; i > 0; i--) {
            if(g_targetFrames[i] < g_currentFrameNr)
                break;
        }
    }
    g_currentTargetFrameIndex = i;
    goToFrame(g_targetFrames[i]);
}
function loadSequence(image_sequence_id, start_frame, nrOfFrames, show_entire_sequence, user_frame_selection, annotate_single_frame, frames_to_annotate, images_to_load_before, images_to_load_after, auto_play) {
    // If user cannot select frame, and there are no target frames, select last frame as target frame
    if(!user_frame_selection && annotate_single_frame && frames_to_annotate.length === 0) {
        // Select last frame as target frame
        frames_to_annotate.push(nrOfFrames-1);
    }
    g_userFrameSelection = user_frame_selection;


    console.log('In load sequence');
    // Create play/pause button
    setPlayButton(auto_play);
    $("#playButton").click(function() {
        setPlayButton(!g_isPlaying);
        if(g_isPlaying) // Start it again
            incrementFrame();
    });

    // Create canvas
    var canvas = document.getElementById('canvas');
    canvas.setAttribute('width', g_canvasWidth);
    canvas.setAttribute('height', g_canvasHeight);
    // IE stuff
    if(typeof G_vmlCanvasManager != 'undefined') {
        canvas = G_vmlCanvasManager.initElement(canvas);
    }
    g_context = canvas.getContext("2d");

    if(g_targetFrames.length > 0) {
        g_currentFrameNr = g_targetFrames[0];
    } else {
        g_currentFrameNr = 0;
    }

    var start;
    var end;
    var totalToLoad;
    if(show_entire_sequence || !annotate_single_frame) {
        start = start_frame;
        end = start_frame + nrOfFrames - 1;
        totalToLoad = nrOfFrames;
    } else {
        start = max(start_frame, g_currentFrameNr - images_to_load_before);
        end = min(start_frame + nrOfFrames - 1, g_currentFrameNr + images_to_load_after);
        totalToLoad = end - start;
    }
    g_startFrame = start;
    g_sequenceLength = end-start;
    console.log("Start frame = " + toString(g_startFrame) + ", sequence length = " + toString(g_sequenceLength));

    // Create slider
    $("#slider").slider(
            {
                range: "max",
                min: start,
                max: end,
                step: 1,
                value: g_currentFrameNr,
            slide: function(event, ui) {
                g_currentFrameNr = ui.value;
                $('#currentFrame').text(g_currentFrameNr);
                setPlayButton(false);
                redrawSequence();
            }
            }
    );

    // Create progress bar
    g_progressbar = $( "#progressbar" );
    var progressLabel = $(".progress-label");
    g_progressbar.progressbar({
      value: false,
      change: function() {
        progressLabel.text( "Please wait while loading. " + g_progressbar.progressbar( "value" ).toFixed(1) + "%" );
      },
      complete: function() {
            // Remove progress bar and redraw
            progressLabel.text( "Finished loading!" );
            g_progressbar.hide();
            redrawSequence();
            g_progressbar.trigger('markercomplete');
            if(g_isPlaying)
                incrementFrame();
      }
    });

    for(var i = 0; i < frames_to_annotate.length; ++i) {
        addKeyFrame(frames_to_annotate[i]);
    }

    $("#addFrameButton").click(function() {
        setPlayButton(false);
        addKeyFrame(g_currentFrameNr);
        g_currentTargetFrameIndex = g_targetFrames.length-1;
    });

    $("#removeFrameButton").click(function() {
        setPlayButton(false);
        if(g_targetFrames.includes(g_currentFrameNr)) {
            g_targetFrames.splice(g_targetFrames.indexOf(g_currentFrameNr), 1);
            g_currentTargetFrameIndex = -1;
            $('#sliderMarker' + g_currentFrameNr).remove();
            $('#selectedFrames' + g_currentFrameNr).remove();
            $('#selectedFramesForm' + g_currentFrameNr).remove();
        }
    });



    $("#nextFrameButton").click(function() {
        goToNextKeyFrame();
    });

    // Moving between frames
    // Scrolling (mouse must be over canvas)
    $("#canvas").bind('mousewheel DOMMouseScroll', function(event){
        g_shiftKeyPressed = event.shiftKey;
        console.log('Mousewheel event!');
        if(event.originalEvent.wheelDelta > 0 || event.originalEvent.detail < 0) {
            // scroll up
            if(g_shiftKeyPressed) {
                goToNextKeyFrame();
            } else {
                goToFrame(g_currentFrameNr + 1);
            }
        } else {
            // scroll down
            if(g_shiftKeyPressed) {
                goToPreviousKeyFrame();
            } else {
                goToFrame(g_currentFrameNr - 1);
            }
        }
        event.preventDefault();
    });

    // Arrow key pressed
    $(document).keydown(function(event){
        g_shiftKeyPressed = event.shiftKey;
        if(event.which === 37) { // Left
            if(g_shiftKeyPressed) {
                goToPreviousKeyFrame();
            } else {
                goToFrame(g_currentFrameNr - 1);
            }
        } else if(event.which === 39) { // Right
            if(g_shiftKeyPressed) {
                goToNextKeyFrame();
            } else {
                goToFrame(g_currentFrameNr + 1);
            }
        }
    });

    $(document).keyup(function(event) {
        g_shiftKeyPressed = event.shiftKey;
    });


    // Load images
    g_framesLoaded = 0;
    //console.log('start: ' + start + ' end: ' + end)
    //console.log('target_frame: ' + target_frame)
    for(var i = start; i <= end; i++) {
        var image = new Image();
        image.src = '/show_frame/' + image_sequence_id + '/' + i + '/' + g_taskID + '/';
        image.onload = function() {
            g_canvasWidth = this.width;
            g_canvasHeight = this.height;
            canvas.setAttribute('width', g_canvasWidth);
            canvas.setAttribute('height', g_canvasHeight);

            // Update progressbar
            g_framesLoaded++;
            g_progressbar.progressbar( "value", g_framesLoaded*100/totalToLoad);
        };
        g_sequence.push(image);
    }
}

function redrawSequence() {
    var index = g_currentFrameNr - g_startFrame;
    g_context.drawImage(g_sequence[index], 0, 0, g_canvasWidth, g_canvasHeight); // Draw background image
}

// using jQuery
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function setReturnURL(url) {
    g_returnURL = url;
}

function colorToHexString(red, green, blue) {
    red = red.toString(16);
    if(red.length == 1) {
        red = "0" + red;
    }
    green = green.toString(16);
    if(green.length == 1) {
        green = "0" + green;
    }
    blue = blue.toString(16);
    if(blue.length == 1) {
        blue = "0" + blue;
    }
    return '#' + red + green + blue;
}

function addLabelButton(label_id, red, green, blue, parent_id) {
    var labelButton = {
        id: label_id,
        red: red,
        green: green,
        blue: blue,
        parent_id: parent_id,
    };
    g_labelButtons.push(labelButton);

    $("#labelButton" + label_id).css("background-color", colorToHexString(red, green, blue));

    // TODO finish
    if(parent_id != 0) {
        $('#sublabel_' + parent_id).hide();
    }
}

function getLabelWithId(id) {
    for(var i = 0; i < g_labelButtons.length; i++) {
        if (g_labelButtons[i].id == id) {
            return g_labelButtons[i];
        }
    }
}

function getLabelList(label) {
    var currentLabel = label;
    var labels = [];
    labels.push(label);
    while(currentLabel.parent_id != 0) {
        currentLabel = getLabelWithId(currentLabel.parent_id);
        labels.push(currentLabel);
    }

    return labels;
}

function showLabelList(list) {
    // Hide all sublabel groups first
    for(var i = 0; i < g_labelButtons.length; i++)  {
        if(g_labelButtons[i].parent_id != 0) {
            $('#sublabel_' + g_labelButtons[i].parent_id).hide();
        }
    }
    // Then show the ones needed
    for(var i = 0; i < list.length; i++) {
        console.log("Showing sublabel group " + list[i].id);
        $('#sublabel_' + list[i].id).show();
    }
}

function decorateLabelButtons(list) {
    // Remove active class from all first
    for(var i = 0; i < g_labelButtons.length; i++)  {
        $('#labelButton' + g_labelButtons[i].id).removeClass('activeLabel');
    }
    // Then add it the ones which have been selected
    for(var i = 0; i < list.length; i++) {
        $('#labelButton' + list[i].id).addClass('activeLabel');
    }
}

function changeLabel(label_id) {
    for(var i = 0; i < g_labelButtons.length; i++)  {
        if(g_labelButtons[i].id == label_id) {
            // Hide previous label's sublabels
            var labelList = getLabelList(g_labelButtons[i]);
            showLabelList(labelList);

            g_currentLabel = label_id;
            // Show new label's sublabels

            var label = g_labelButtons[i];
            // Set correct button to active
            decorateLabelButtons(labelList);
            //$('#labelButton' + label.id).addClass('activeLabel');
            g_currentColor = {
                red: label.red,
                green: label.green,
                blue: label.blue
            };
            console.log(i + ' is now active label');
            break;
        }
    }
}

function changeImage(url) {
    if(g_annotationHasChanged) {
        // Open dialog
        g_nextURL = url;
        $('#dialogConfirm').dialog("open");
    } else {
        window.location.href = url;
    }
}
