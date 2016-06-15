var context;
var canvasWidth = 512;
var canvasHeight = 512;
var sequence = new Array();
var currentFrameNr;
var progressbar;

function loadSequence(image_sequence_id, nrOfFrames) {

    // Create canvas
    var canvas = document.getElementById('canvas');
    canvas.setAttribute('width', canvasWidth);
    canvas.setAttribute('height', canvasHeight);
    // IE stuff
    if(typeof G_vmlCanvasManager != 'undefined') {
        canvas = G_vmlCanvasManager.initElement(canvas);
    }
    context = canvas.getContext("2d");

    currentFrameNr = 0;

    // Create slider
    $("#slider").slider(
            {
                range: "max",
                min: 0,
                max: nrOfFrames,
                step: 1,
                value: currentFrameNr,
            slide: function(event, ui) {
                currentFrameNr = ui.value;
                redrawSequence();
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
            redrawSequence();
      }
    });

    $("#addFrameButton").click(function() {
        console.log('weee' + currentFrameNr);
        $("#framesSelected").append('<li>' + currentFrameNr + '</li>');
        $("#framesForm").append('<input type="hidden" name="frames" value="' + currentFrameNr + '">');
    });

    // Load images
    framesLoaded = 0;
    console.log('Hmm' + nrOfFrames)
    for(var i = 0; i < nrOfFrames; i++) {
        var image = new Image();
        image.src = '/annotation/show_frame/' + image_sequence_id + '/' + i + '/';
        image.onload = function() {
            canvasWidth = this.width;
            canvasHeight = this.height;
            canvas.setAttribute('width', canvasWidth);
            canvas.setAttribute('height', canvasHeight);

            // Update progressbar
            framesLoaded++;
            progressbar.progressbar( "value", framesLoaded*100/nrOfFrames);
        }

        sequence.push(image);
    }
}

function redrawSequence() {
    context.drawImage(sequence[currentFrameNr], 0, 0, canvasWidth, canvasHeight); // Draw background image
}