// Biến global
let sourceLanguage = 'Vietnamese';
let targetLanguage = 'English';
let uploadedFile = null;

// Khởi tạo danh sách ngôn ngữ
function initLanguageList() {
    const sourceList = document.getElementById('sourceList');
    const targetList = document.getElementById('targetList');
    
    sourceList.innerHTML = '';
    targetList.innerHTML = '';
    
    // languageCodeDict được định nghĩa trong file HTML từ Flask
    if (typeof languageCodeDict !== 'undefined') {
        Object.keys(languageCodeDict).forEach(lang => {
            const sourceLi = document.createElement('li');
            sourceLi.className = 'language-item';
            sourceLi.textContent = lang;
            sourceLi.onclick = () => selectSourceLanguage(lang);
            sourceList.appendChild(sourceLi);
            
            const targetLi = document.createElement('li');
            targetLi.className = 'language-item';
            targetLi.textContent = lang;
            targetLi.onclick = () => selectTargetLanguage(lang);
            targetList.appendChild(targetLi);
        });
    } else {
        console.error("Lỗi: languageCodeDict chưa được định nghĩa.");
    }
}

// Chọn ngôn ngữ nguồn
function selectSourceLanguage(lang) {
    sourceLanguage = lang;
    document.getElementById('sourceLangText').textContent = lang;
    document.getElementById('sourceDropdown').classList.remove('active');
    document.getElementById('sourceLangBtn').classList.remove('active');
    updateSelectedItems();
}

// Chọn ngôn ngữ đích
function selectTargetLanguage(lang) {
    targetLanguage = lang;
    document.getElementById('targetLangText').textContent = lang;
    document.getElementById('targetDropdown').classList.remove('active');
    document.getElementById('targetLangBtn').classList.remove('active');
    updateSelectedItems();
}

// Cập nhật item được chọn
function updateSelectedItems() {
    document.querySelectorAll('#sourceList .language-item').forEach(item => {
        item.classList.toggle('selected', item.textContent === sourceLanguage);
    });
    document.querySelectorAll('#targetList .language-item').forEach(item => {
        item.classList.toggle('selected', item.textContent === targetLanguage);
    });
}

// Toggle dropdown ngôn ngữ nguồn
document.getElementById('sourceLangBtn').onclick = () => {
    const dropdown = document.getElementById('sourceDropdown');
    const button = document.getElementById('sourceLangBtn');
    dropdown.classList.toggle('active');
    button.classList.toggle('active');
    document.getElementById('targetDropdown').classList.remove('active');
    document.getElementById('targetLangBtn').classList.remove('active');
};

// Toggle dropdown ngôn ngữ đích
document.getElementById('targetLangBtn').onclick = () => {
    const dropdown = document.getElementById('targetDropdown');
    const button = document.getElementById('targetLangBtn');
    dropdown.classList.toggle('active');
    button.classList.toggle('active');
    document.getElementById('sourceDropdown').classList.remove('active');
    document.getElementById('sourceLangBtn').classList.remove('active');
};

// Đóng dropdown khi click bên ngoài
document.addEventListener('click', (e) => {
    if (!e.target.closest('.language-dropdown')) {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.classList.remove('active');
        });
        document.querySelectorAll('.language-button').forEach(btn => {
            btn.classList.remove('active');
        });
    }
});

// Toggle Thinking
// Lưu ý: Nếu HTML dùng id="thinkingToggle" nhưng JS lại gọi "thinkingBtn", cần sửa lại cho khớp
const thinkingElement = document.getElementById('thinkingBtn') || document.getElementById('thinkingToggle');

if (thinkingElement) {
    thinkingElement.onclick = async () => {
        try {
            const response = await fetch('/thinking', { method: 'POST' });
            const data = await response.json();

            if (response.ok) {
                if (data.thinking) {
                    showSuccess("🧠 Thinking mode: ON");
                    thinkingElement.classList.add('active');
                    // Nếu là checkbox
                    if(thinkingElement.type === 'checkbox') thinkingElement.checked = true;
                } else {
                    showSuccess("🧠 Thinking mode: OFF");
                    thinkingElement.classList.remove('active');
                    // Nếu là checkbox
                    if(thinkingElement.type === 'checkbox') thinkingElement.checked = false;
                }
            } else {
                showError("Không thể đổi trạng thái Thinking!");
            }
        } catch (error) {
            console.error(error);
            showError("Lỗi kết nối khi đổi Thinking mode!");
        }
    };
}


// Tìm kiếm ngôn ngữ
document.getElementById('sourceSearch').oninput = (e) => {
    filterLanguages('sourceList', e.target.value);
};

document.getElementById('targetSearch').oninput = (e) => {
    filterLanguages('targetList', e.target.value);
};

function filterLanguages(listId, query) {
    const items = document.querySelectorAll(`#${listId} .language-item`);
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query.toLowerCase()) ? 'block' : 'none';
    });
}

// Đổi ngôn ngữ
document.getElementById('swapBtn').onclick = () => {
    const temp = sourceLanguage;
    sourceLanguage = targetLanguage;
    targetLanguage = temp;
    
    document.getElementById('sourceLangText').textContent = sourceLanguage;
    document.getElementById('targetLangText').textContent = targetLanguage;
    
    const tempText = document.getElementById('sourceText').value;
    document.getElementById('sourceText').value = document.getElementById('targetText').value;
    document.getElementById('targetText').value = tempText;
    
    document.getElementById('charCount').textContent = document.getElementById('sourceText').value.length;
    updateSelectedItems();
};

// Đếm ký tự
document.getElementById('sourceText').oninput = (e) => {
    const count = e.target.value.length;
    document.getElementById('charCount').textContent = count;
    
    if (count > 5000) {
        e.target.value = e.target.value.substring(0, 5000);
        document.getElementById('charCount').textContent = 5000;
    }
};

// Upload file
document.getElementById('fileInput').onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    document.getElementById('fileName').textContent = file.name;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/uploadfile', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(`✅ ${data.message}: ${data.filename}`);
        } else {
            showError(data.error || 'Tải file thất bại!');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showError('Không thể tải file lên server!');
    }
};


// Text-to-Speech
document.getElementById('ttsBtn').onclick = async () => {
    const text = document.getElementById('targetText').value.trim();
    
    if (!text) {
        showError('Chưa có bản dịch để chuyển thành giọng nói!');
        return;
    }

    try {
        const speechLang = languageCodeDict[targetLanguage].split('_')[0];
        const response = await fetch('/speed2text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                speech_language: speechLang
            })
        });

        const data = await response.json();
        
        if (response.ok && data.media) {
            const audio = new Audio(data.media);
            audio.play();
        } else {
            showError(data.error || 'Không thể tạo âm thanh!');
        }
    } catch (error) {
        showError('Lỗi khi tạo âm thanh!');
        console.error('TTS error:', error);
    }
};

// Dịch văn bản
async function translate() {
    const text = document.getElementById('sourceText').value.trim();
    const style = document.getElementById('styleSelect').value;
    
    if (!text) {
        showError('Vui lòng nhập văn bản cần dịch!');
        return;
    }
    
    const loading = document.getElementById('loading');
    const translateBtn = document.getElementById('translateBtn');
    const errorMessage = document.getElementById('errorMessage');
    
    loading.classList.add('active');
    translateBtn.disabled = true;
    errorMessage.classList.remove('active');
    
    try {
        const response = await fetch('/translate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                src_language: sourceLanguage,
                fr_language: targetLanguage,
                style: style
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('targetText').value = data.translation;
        } else {
            showError(data.error || 'Có lỗi xảy ra khi dịch!');
        }
    } catch (error) {
        showError('Không thể kết nối đến server. Vui lòng thử lại!');
        console.error('Translation error:', error);
    } finally {
        loading.classList.remove('active');
        translateBtn.disabled = false;
    }
}

function showError(message) {
    const errorEl = document.getElementById('errorMessage');
    errorEl.textContent = '⚠️ ' + message;
    errorEl.classList.add('active');
    setTimeout(() => {
        errorEl.classList.remove('active');
    }, 5000);
}

function showSuccess(message) {
    const msgBox = document.createElement('div');
    msgBox.textContent = message;
    msgBox.style.position = 'fixed';
    msgBox.style.bottom = '20px';
    msgBox.style.right = '20px';
    msgBox.style.padding = '12px 20px';
    msgBox.style.background = 'linear-gradient(135deg, #4CAF50, #81C784)';
    msgBox.style.color = 'white';
    msgBox.style.borderRadius = '8px';
    msgBox.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
    msgBox.style.zIndex = 2000;
    msgBox.style.transition = 'opacity 0.3s ease';
    document.body.appendChild(msgBox);
    setTimeout(() => {
        msgBox.style.opacity = 0;
        setTimeout(() => msgBox.remove(), 500);
    }, 4000);
}

// Gửi phản hồi Like / Dislike
async function sendFeedback(isLike) {
    const srcText = document.getElementById('sourceText').value.trim();
    const translateText = document.getElementById('targetText').value.trim();
    const style = document.getElementById('styleSelect').value;

    if (!srcText || !translateText) {
        showError('Không có dữ liệu để gửi phản hồi!');
        return;
    }

    try {
        const response = await fetch('/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                src_text: srcText,
                translate_text: translateText,
                style: style,
                type: isLike ? 1 : 0
            })
        });

        const data = await response.json();

        if (response.ok) {
            showSuccess(isLike ? '✅ Đã lưu phản hồi Like!' : '❌ Đã lưu phản hồi Dislike!');
        } else {
            showError(data.error || 'Không thể lưu phản hồi!');
        }
    } catch (error) {
        console.error('Feedback error:', error);
        showError('Lỗi khi gửi phản hồi!');
    }
}

// Gán sự kiện click
document.getElementById('likeBtn').onclick = () => sendFeedback(true);
document.getElementById('dislikeBtn').onclick = () => sendFeedback(false);

document.getElementById('translateBtn').onclick = translate;

document.getElementById('sourceText').onkeydown = (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        translate();
    }
};

// Khởi tạo
document.addEventListener('DOMContentLoaded', () => {
    initLanguageList();
    updateSelectedItems();
});