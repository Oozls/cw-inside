document.addEventListener("DOMContentLoaded", function () {
    const editor = new toastui.Editor({
        el: document.querySelector('#editor'),
        height: '500px',
        initialEditType: 'wysiwyg',
        previewStyle: 'tab',
        hideModeSwitch: true,
        language: 'ko-KR',
        hooks: {
            async addImageBlobHook(blob, callback) {
                const formData = new FormData();
                formData.append('image', blob);

                const res = await fetch('/upload_image', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();
                callback(data.url, 'image');
            }
        }
    });

    document.querySelector('#post_form').addEventListener('submit', function(e) {
        const htmlContent = editor.getHTML();
        document.querySelector('#content').value = htmlContent;
        console.log("콘텐츠:", document.querySelector('#content').value);
    });
})