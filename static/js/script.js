// اضافه کردن متدهای کمکی برای چت‌بات

// تبدیل متن ساده به HTML با پشتیبانی از Markdown
function renderMarkdown(text) {
    return marked.parse(text);
}

// بررسی اینکه آیا متن شامل کاراکترهای RTL است یا نه
function isRTL(text) {
    const rtlChars = /[\u0591-\u07FF\u200F\u202B\u202E\uFB1D-\uFDFD\uFE70-\uFEFC]/;
    return rtlChars.test(text);
}

// اسکرول کردن به آخرین پیام
function scrollToBottom() {
    const chatBox = document.getElementById("chat-box");
    chatBox.scrollTop = chatBox.scrollHeight;
}

// فرمت کردن زمان برای پیام‌ها
function formatTime() {
    const date = new Date();
    return date.getHours().toString().padStart(2, '0') + ":" + 
           date.getMinutes().toString().padStart(2, '0');
}

// پردازش کلیدهای میانبر
function handleShortcuts(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// مدیریت ارسال پیام و دریافت پاسخ
async function sendMessage() {
    const userInput = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const message = userInput.value.trim();

    if (message === "") {
        return;
    }

    // نمایش پیام کاربر
    chatBox.innerHTML += `
        <div class='message user'>
            ${message}
            <span class='time'>${formatTime()}</span>
        </div>
    `;

    // پاک کردن ورودی کاربر
    userInput.value = "";

    // اسکرول به پایین
    scrollToBottom();

    // نمایش انیمیشن لودینگ
    chatBox.innerHTML += `
        <div class='message bot loading'>
            <span>در حال پردازش...</span>
            <i class='fas fa-circle-notch'></i>
        </div>
    `;
    scrollToBottom();

    try {
        // ارسال پیام به سرور
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body: `user_input=${encodeURIComponent(message)}`
        });

        const data = await response.json();

        // حذف انیمیشن لودینگ
        const loadingMessage = document.querySelector(".loading");
        if (loadingMessage) {
            loadingMessage.remove();
        }

        // تشخیص جهت متن پاسخ
        const messageClass = isRTL(data.response) ? 'rtl' : 'ltr';

        // تبدیل متن به HTML با استفاده از marked
        const formattedResponse = renderMarkdown(data.response);

        // نمایش پاسخ چت‌بات
        chatBox.innerHTML += `
            <div class='message bot ${messageClass}'>
                ${formattedResponse}
                <span class='time'>${formatTime()}</span>
            </div>
        `;
        scrollToBottom();

    } catch (error) {
        console.error("Error:", error);
        
        // حذف انیمیشن لودینگ
        const loadingMessage = document.querySelector(".loading");
        if (loadingMessage) {
            loadingMessage.remove();
        }

        // نمایش پیام خطا
        chatBox.innerHTML += `
            <div class='message bot error'>
                متأسفانه در پردازش درخواست شما مشکلی پیش آمد. لطفاً دوباره تلاش کنید.
            </div>
        `;
        scrollToBottom();
    }
}

// اضافه کردن هندلرهای رویداد
document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById("user-input");
    
    // Event listener برای ارسال با کلید Enter
    if (userInput) {
        userInput.addEventListener("keypress", handleShortcuts);
    }
});