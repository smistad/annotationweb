var context;
var canvasWidth = 512;
var canvasHeight = 512;
var sequence = new Array();
var currentFrameNr;
var progressbar;
var framesLoaded;

function max(a, b) {
    return a > b ? a : b;
}

function min(a, b) {
    return a < b ? a : b;
}

function loadSequence(image_sequence_id, nrOfFrames, target_frame = 0, images_to_load = 0) {

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

    var start = 0;
    var end = nrOfFrames-1;
    var totalToLoad = nrOfFrames;
    if(images_to_load > 0) {
        start = max(0, target_frame - images_to_load);
        end = min(nrOfFrames - 1, target_frame + images_to_load);
        totalToLoad = end - start;
    }

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
                redrawSequence(start);
            }
            }
    )/*.each(function() {
        var options = $(this).data().uiSlider.options;

        var nrOfValues = options.max - options.min;

        for(var i = 0; i < nrOfValues; i++) {
            var element;
            if(i+options.min == frameToSegment) {
                element = $('<label>' + (i + options.min) + '</label>').css('left', (i*100/nrOfValues) + '%').css('font-weight', 'bold');
            } else if(i == 0) {
                element = $('<label>' + (i + options.min) + '</label>').css('left', (i*100/nrOfValues) + '%');
            } else if(i == nrOfValues-1) {
                element = $('<label>' + (i + options.min) + '</label>').css('left', (i*100/nrOfValues) + '%');
            } else {
                element = $('<label>' + '</label>').css('left', (i*100/nrOfValues) + '%');
            }
            $("#slider").append(element);
        }
    })*/;

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
            redrawSequence(start);
      }
    });

    $("#addFrameButton").click(function() {
        $("#framesSelected").append('<li>' + currentFrameNr + '</li>');
        $("#framesForm").append('<input type="hidden" name="frames" value="' + currentFrameNr + '">');
    });

    $("#goToTargetFrame").click(function() {
        currentFrameNr = target_frame;
        $('#slider').slider('value', target_frame); // Update slider
        redrawSequence(start);
    });

    // Load images
    framesLoaded = 0;
    //console.log('start: ' + start + ' end: ' + end)
    //console.log('target_frame: ' + target_frame)
    for(var i = start; i <= end; i++) {
        var image = new Image();
        image.src = '/annotation/show_frame/' + image_sequence_id + '/' + i + '/';
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

function redrawSequence(startFrame) {
    var index = currentFrameNr - startFrame;
    //console.log('index: ' + index)
    context.drawImage(sequence[index], 0, 0, canvasWidth, canvasHeight); // Draw background image
}