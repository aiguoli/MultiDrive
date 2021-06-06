const text2mark = () => {
    const textElement = document.getElementById('readme');
    if (textElement) {
        textElement.innerHTML = marked(textElement.getAttribute('value'));
    }
}

const filePreview = () => {
    const url = document.getElementById('downloadUrl').value;
    const previewElement = document.getElementById('preview');
    switch (previewElement.dataset.fileType) {
        case 'image':
            const image = document.createElement('img');
            image.src = url;
            image.className = 'preview';
            previewElement.appendChild(image);
            break;
        case 'video':
            const video = document.createElement('div');
            video.id = 'dplayer';
            previewElement.appendChild(video);
            const dp = new DPlayer({
                container: video,
                screenshot: true,
                video: {
                    url: document.getElementById('downloadUrl').value
                }
            })
            break;
        case 'audio':
            const audio = document.createElement('audio');
            audio.src = document.getElementById('downloadUrl').value;
            audio.controls = true;
            audio.style.width = '100%';
            previewElement.appendChild(audio);
            break;
        case 'text':
            fetch(url)
                .then(function (response) {
                    return response.text()
                })
                .then(function (fileContent) {
                    previewElement.innerText = fileContent;
                });
            break;
        case 'office':
            const officeView = document.createElement('iframe');
            officeView.src = 'https://view.officeapps.live.com/op/view.aspx?src='+encodeURIComponent(url);
            officeView.width = '100%';
            officeView.height = '100%';
            previewElement.appendChild(officeView);
    }
}



text2mark()
filePreview()
