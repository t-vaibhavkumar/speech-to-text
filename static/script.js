


let mediaRecorder;
let audioChunks = [];

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.start();
            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };
        });
}

function stopRecording() {
    mediaRecorder.stop();
    mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

        const formData = new FormData();
        formData.append('audio_data', audioBlob, 'audio.webm');

        fetch('/transcribe', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(transcription => {
            $('#transcription').text(transcription);
        })
        .catch(error => {
            console.error('Error:', error);
        });

        // Reset audioChunks array
        audioChunks = [];
    };
}

$(document).ready(() => {
    $('#startRecording').click(() => {
        startRecording();
        $('#startRecording').prop('disabled', true);
        $('#stopRecording').prop('disabled', false);
    });

    $('#stopRecording').click(() => {
        stopRecording();
        $('#startRecording').prop('disabled', false);
        $('#stopRecording').prop('disabled', true);
    });
});
