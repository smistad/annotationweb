var context;
var canvasWidth = 512;
var canvasHeight = 512;
var sequence = new Array();
var currentFrameNr;
var startFrame;
var progressbar;
var framesLoaded;
var is_playing = true;
var g_returnURL = '';

function max(a, b) {
    return a > b ? a : b;
}

function min(a, b) {
    return a < b ? a : b;
}

function incrementFrame() {
    currentFrameNr = ((currentFrameNr-startFrame) + 1) % framesLoaded + startFrame;
    $('#slider').slider('value', currentFrameNr); // Update slider
    redrawSequence();
    if(is_playing)
        window.setTimeout(incrementFrame, 50);
}

function setPlayButtonText() {
    if(is_playing) {
        $("#playButton").html('Pause');
    } else {
        $("#playButton").html('Play');
    }
}

function save() {
    var messageBox = document.getElementById("message")
    messageBox.innerHTML = '<span class="info">Please wait while saving..</span>';
    sendDataForSave().done(function(data) {
        console.log("Save done..");
        console.log(data);
        var messageBox = document.getElementById("message")
        if(data.success == "true") {
            messageBox.innerHTML = '<span class="success">Image was saved</span>';
            if(g_returnURL != '') {
                window.location = g_returnURL;
            } else {
                // Reset image quality form before refreshing
                $('#imageQualityForm')[0].reset();
                // Refresh page
                location.reload();
            }
        } else {
            messageBox.innerHTML = '<span class="error">Save failed! ' + data.message + '</span>';
        }
        console.log(data.message);
    }).fail(function(data) {
        console.log("Ajax failed");
        var messageBox = document.getElementById("message")
        messageBox.innerHTML = '<span class="error">Save failed!</span>';
    }).always(function(data) {
        console.log("Ajax complete");
    });
    console.log("Save function executed");
}

function initializeAnnotation() {
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
}

function loadSequence(image_sequence_id, nrOfFrames, target_frame, show_entire_sequence, images_to_load_before, images_to_load_after, auto_play) {
    console.log('In load sequence');
    is_playing = auto_play;
    // Create play/pause button
    setPlayButtonText();
    $("#playButton").click(function() {
        is_playing = !is_playing;
        setPlayButtonText();
        if(is_playing) // Start it again
            incrementFrame();
    });

    // Create canvas
    var canvas = document.getElementById('canvas');
    canvas.setAttribute('width', canvasWidth);
    canvas.setAttribute('height', canvasHeight);
    // IE stuff
    if(typeof G_vmlCanvasManager != 'undefined') {
        canvas = G_vmlCanvasManager.initElement(canvas);
    }
    context = canvas.getContext("2d");

    currentFrameNr = target_frame;

    var start;
    var end;
    var totalToLoad;
    if(show_entire_sequence) {
        start = 0;
        end = nrOfFrames-1;
        totalToLoad = nrOfFrames;
    } else {
        start = max(0, target_frame - images_to_load_before);
        end = min(nrOfFrames - 1, target_frame + images_to_load_after);
        totalToLoad = end - start;
    }
    startFrame = start;

    // Create slider
    $("#slider").slider(
            {
                range: "max",
                min: start,
                max: end,
                step: 1,
                value: currentFrameNr,
            slide: function(event, ui) {
                currentFrameNr = ui.value;
                redrawSequence();
            }
            }
    );

    // Create progress bar
    progressbar = $( "#progressbar" );
    progressLabel = $(".progress-label");
    progressbar.progressbar({
      value: false,
      change: function() {
        progressLabel.text( "Please wait while loading. " + progressbar.progressbar( "value" ).toFixed(1) + "%" );
      },
      complete: function() {
            // Remove progress bar and redraw
            progressLabel.text( "Finished loading!" );
            progressbar.hide();
            redrawSequence();
            if(is_playing)
                incrementFrame();
      }
    });

    $("#addFrameButton").click(function() {
        $("#framesSelected").append('<li>' + currentFrameNr + '</li>');
        $("#framesForm").append('<input type="hidden" name="frames" value="' + currentFrameNr + '">');
    });

    $("#goToTargetFrame").click(function() {
        currentFrameNr = target_frame;
        $('#slider').slider('value', target_frame); // Update slider
        redrawSequence();
    });


    // Load images
    framesLoaded = 0;
    //console.log('start: ' + start + ' end: ' + end)
    //console.log('target_frame: ' + target_frame)
    for(var i = start; i <= end; i++) {
        var image = new Image();
        image.src = '/show_frame/' + image_sequence_id + '/' + i + '/';
        image.onload = function() {
            canvasWidth = this.width;
            canvasHeight = this.height;
            canvas.setAttribute('width', canvasWidth);
            canvas.setAttribute('height', canvasHeight);

            // Update progressbar
            framesLoaded++;
            progressbar.progressbar( "value", framesLoaded*100/totalToLoad);
        }

        sequence.push(image);
    }

}

function redrawSequence() {
    var index = currentFrameNr - startFrame;
    context.drawImage(sequence[index], 0, 0, canvasWidth, canvasHeight); // Draw background image
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
