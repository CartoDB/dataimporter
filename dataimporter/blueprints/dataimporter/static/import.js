(function($) {
    $(document).ready(() => {
        var bars =   {};

        function progressHandlingFunction(e) {
            if (e.lengthComputable) {
                console.log(e.loaded);
                var progress = e.loaded / e.total;
                bars['pb-container'].animate(progress);
            }
        };

        function createProgressBar(containerId) {
            var template = '<div class="row pb">' +
                '<div class= "pb-container" id="' + containerId + '"></div>' +
                '</div>';
            $('.row.conf').after($(template).clone());
            var bar = new ProgressBar.Line('#' + containerId, {
                strokeWidth: 4,
                easing: 'easeInOut',
                duration: 1400,
                color: '#FFEA82',
                trailColor: '#eee',
                trailWidth: 1,
                svgStyle: { width: '100%', height: '100%' },
                text: {
                    style: {
                        color: '#999',
                        position: 'absolute',
                        right: '0',
                        top: '30px',
                        padding: 0,
                        margin: 0,
                        transform: null
                    },
                    autoStyleContainer: false
                },
                from: { color: '#FFEA82' },
                to: { color: '#ED6A5A' },
                step: (state, bar) => {
                    bar.setText(Math.round(bar.value() * 100) + ' %');
                }
            });

            bar.text.style.fontFamily = '"Raleway", Helvetica, sans-serif';
            bar.text.style.fontSize = '2rem';
            return bar;
        };

        $(document).on('submit', 'form', (event) => {
            event.preventDefault();
            var $form = $('form');
            var formData = new FormData($form[0]);
            var csrfToken = $form.find('#csrf_token').val();

            var containerId = 'pb-container';
            bars[containerId] = createProgressBar(containerId);

            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrfToken)
                    }
                }
            });

            // send via ajax this data
            $.ajax({
                url: "/import/",
                type: "POST",

                // progress handling start
                xhr: function() { // Custom XMLHttpRequest
                    var myXhr = $.ajaxSettings.xhr();
                    if (myXhr.upload) { // Check if upload property exists
                        myXhr.upload.addEventListener('progress', progressHandlingFunction, false); // For handling the progress of the upload
                    } else {
                        console.log("Upload progress is not supported!");
                    }
                    return myXhr;
                },

                // ajax events
                // beforeSend: beforeSendHandler,
                // success: completeHandler,
                // error: errorHandler,
                // progress handling ends

                data: formData,
                cache: false,
                // async: false,
                processData: false,
                contentType: false,
                success: function(response) {
                    // console.log(response);
                    // window.location.reload(true);

                }
            });
            return false;
        });
    });
}(jQuery));