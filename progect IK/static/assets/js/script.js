document.addEventListener('DOMContentLoaded', function () {



    

    // References to all the element we will need.
    var video = document.querySelector('video'),
        canvas = document.getElementById('canvas'),
        image = document.querySelector('#snap'),
        take_photo_btn = document.querySelector('#take-photo')
        start_camera = document.querySelector('#start-camera'),
        controls = document.querySelector('.controls'),
        delete_photo_btn = document.querySelector('#delete-photo'),
        download_photo_btn = document.querySelector('#download-photo'),
        error_message = document.querySelector('#error-message');


    // The getUserMedia interface is used for handling camera input.
    // Some browsers need a prefix so here we're covering all the options
    navigator.getMedia = ( navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia);


    if(!navigator.getMedia){
        displayErrorMessage("Your browser doesn't have support for the navigator.getUserMedia interface.");
    }
    else{

        // Request the camera.
        navigator.getMedia(
            {
                video: true
            },
            // Success Callback
            function(stream){

                // Create an object URL for the video stream and
                // set it as src of our HTLM video element.
                video.srcObject = stream;

                // Play the video element to start the stream.
                video.play();
                video.onplay = function() {
                    showVideo();
                };
         
            },
            // Error Callback
            function(err){
                displayErrorMessage("Произошла ошибка доступа к потоку камеры: " + err.name, err);
            }
        );

    }



    // Mobile browsers cannot play video without user input,
    // so here we're using a button to start it manually.
    start_camera.addEventListener("click", function(e){

        e.preventDefault();

        // Start video playback manually.
        video.play();
        showVideo();

    });


    take_photo_btn.addEventListener("click", function(e){

        e.preventDefault();

        var snap = takeSnapshot();
        // console.log(snap);
        // console.log(typeof(snap));

        // Show image. 
        image.setAttribute('src', snap);
        image.classList.add("visible");

        // Enable delete and save buttons
        delete_photo_btn.classList.remove("disabled");
        // download_photo_btn.classList.remove("disabled");

        // Set the href attribute of the download button to the snap url.
        take_photo_btn.href = snap;

        const cnv = document.createElement('canvas'),
            ctx = cnv.getContext('2d');

        ctx.drawImage(video, 0,0);

        var data = canvas.toBlob((data) => {
            console.log(data);
            console.log(typeof(data));
            var form_data = new FormData();
            form_data.append("file", data, "image/png")
            fetch('http://127.0.0.1:5000/cam', {
                method: 'POST',
                body: form_data
            }).then(() => {
                location.reload();
            });
        });
        
        // var data = canvas.toBlob((data) => {
        //     console.log(data);
        //     console.log(typeof(data));
        //     a = new FormData();
        //     a.append("file", data, "image/png")
        //     fetch('http://127.0.0.1:5000/cam', {
        //         method: 'post',
        //         mode: 'no-cors',
        //         body: a
        //     });
        // });



        // Pause video playback of stream.
        video.pause();
                // location.reload(); 
        // return false;

    });


    





    delete_photo_btn.addEventListener("click", function(e){

        e.preventDefault();

        // Hide image.
        image.setAttribute('src', "");
        image.classList.remove("visible");

        // Disable delete and save buttons
        delete_photo_btn.classList.add("disabled");
        download_photo_btn.classList.add("disabled");

        // Resume playback of stream.
        video.play();

    });


  
    function showVideo(){
        // Display the video stream and the controls.

        hideUI();
        video.classList.add("visible");
        controls.classList.add("visible");
    }


    function takeSnapshot(){
        // Here we're using a trick that involves a hidden canvas element.  

        var hidden_canvas = document.querySelector('canvas'),
            context = hidden_canvas.getContext('2d');

        var width = video.videoWidth,
            height = video.videoHeight;

        if (width && height) {

            // Setup a canvas with the same dimensions as the video.
            hidden_canvas.width = width;
            hidden_canvas.height = height;

            // Make a copy of the current frame in the video on the canvas.
            context.drawImage(video, 0, 0, width, height);

            // Turn the canvas image into a dataURL that can be used as a src for our photo.
            return hidden_canvas.toDataURL('image/png');
        }
    }


    function displayErrorMessage(error_msg, error){
        error = error || "";
        if(error){
            console.error(error);
        }

        error_message.innerText = error_msg;

        hideUI();
        error_message.classList.add("visible");
    }

   
    function hideUI(){
        // Helper function for clearing the app UI.

        controls.classList.remove("visible");
        start_camera.classList.remove("visible");
        video.classList.remove("visible");
        snap.classList.remove("visible");
        error_message.classList.remove("visible");
    }

});



