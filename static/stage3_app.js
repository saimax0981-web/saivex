let conversations = [];
let activeConversationId = null;
let lastUserMessage = "";

function toggleSidebar(){
    document.getElementById("sidebar").classList.toggle("open");
    document.getElementById("overlay").classList.toggle("show");
}

function closeSidebarMobile(){
    if(window.innerWidth <= 800){
        document.getElementById("sidebar").classList.remove("open");
        document.getElementById("overlay").classList.remove("show");
    }
}

function setPrompt(text){
    document.getElementById("message").value = text;
    document.getElementById("message").focus();
}

function hideEmptyState(){
    let empty = document.getElementById("emptyState");
    if(empty) empty.remove();
}

function formatMessage(text){
    return String(text)
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replace(/\n/g,"<br>");
}

function addUserMessage(message){
    hideEmptyState();
    let chatbox = document.getElementById("chatbox");
    chatbox.innerHTML += `<div class="message-row"><div class="user">${formatMessage(message)}</div></div>`;
    chatbox.scrollTop = chatbox.scrollHeight;
}

function addBotMessage(message, image="", file="", preview=""){
    hideEmptyState();

    let extra = "";

    if(image){
        extra += `<br><br>
        <img src="${image}" class="generated-image">
        <div class="image-actions">
            <a href="${image}" target="_blank" class="view-btn">View</a>
            <a href="${image}" download class="download-btn">Download</a>
        </div>`;
    }

    if(file || preview){
        extra += `<div class="file-actions">`;
        if(file) extra += `<a href="${file}" target="_blank" class="file-btn">Download File</a>`;
        if(preview) extra += `<a href="${preview}" target="_blank" class="preview-btn">Preview</a>`;
        extra += `</div>`;
    }

    let chatbox = document.getElementById("chatbox");
    chatbox.innerHTML += `<div class="message-row"><div class="bot">${formatMessage(message)}${extra}</div></div>`;
    chatbox.scrollTop = chatbox.scrollHeight;
}

function removeLastBot(){
    let bots = document.querySelectorAll(".bot");
    if(bots.length > 0){
        bots[bots.length - 1].parentElement.remove();
    }
}

async function sendMessage(){
    let input = document.getElementById("message");
    let msg = input.value.trim();

    if(!msg) return;

    lastUserMessage = msg;

    addUserMessage(msg);
    input.value = "";

    addBotMessage("Saivex is thinking...");

    try{
        let response = await fetch("/chat", {
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({
                message:msg,
                conversation_id:activeConversationId,
                style:document.getElementById("imageStyle").value,
                ratio:document.getElementById("imageRatio").value
            })
        });

        let data = await response.json();

        removeLastBot();

        activeConversationId = data.conversation_id;

        addBotMessage(data.reply, data.image, data.file_url, data.preview_url);

        speakText(data.reply);

        loadConversations();
        loadMemories();
        loadDocuments();

    }catch(error){
        removeLastBot();
        addBotMessage("Something went wrong. Please check the terminal error.");
        console.log(error);
    }
}

function speakText(text){
    if(!("speechSynthesis" in window)) return;

    speechSynthesis.cancel();

    let speech = new SpeechSynthesisUtterance(text);
    speech.lang = "en-US";
    speech.rate = 1;
    speech.pitch = 1;

    speechSynthesis.speak(speech);
}

function startVoice(){
    if(!("webkitSpeechRecognition" in window)){
        alert("Voice works best in Google Chrome.");
        return;
    }

    let recognition = new webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();

    recognition.onresult = function(event){
        document.getElementById("message").value = event.results[0][0].transcript;
    };
}

function uploadFile(){
    document.getElementById("fileInput").click();
}

function uploadImage(){
    document.getElementById("imageInput").click();
}

async function handleFileUpload(){
    let input = document.getElementById("fileInput");

    if(input.files.length === 0) return;

    let file = input.files[0];

    addUserMessage("Uploaded document: " + file.name);
    addBotMessage("Reading your file...");

    let formData = new FormData();
    formData.append("file", file);

    try{
        let response = await fetch("/upload", {
            method:"POST",
            body:formData
        });

        let data = await response.json();

        removeLastBot();
        addBotMessage(data.reply);

        input.value = "";

        loadDocuments();
    }catch(error){
        removeLastBot();
        addBotMessage("Document upload failed.");
        console.log(error);
    }
}

async function handleImageUpload(){
    let input = document.getElementById("imageInput");

    if(input.files.length === 0) return;

    let image = input.files[0];

    addUserMessage("Uploaded image: " + image.name);
    addBotMessage("Saivex Vision is analyzing your image...");

    let formData = new FormData();
    formData.append("image", image);

    try{
        let response = await fetch("/upload_image", {
            method:"POST",
            body:formData
        });

        let data = await response.json();

        removeLastBot();

        addBotMessage(data.reply, data.image);

        input.value = "";

        loadConversations();

    }catch(error){
        removeLastBot();
        addBotMessage("Image upload failed. Please check your terminal.");
        console.log(error);
    }
}

async function loadConversations(){
    let response = await fetch("/conversations");
    conversations = await response.json();
    renderConversations();
}

function renderConversations(){
    let panel = document.getElementById("conversationPanel");
    let search = document.getElementById("searchBox").value.toLowerCase();

    panel.innerHTML = "";

    conversations
        .filter(c => c.title.toLowerCase().includes(search) || c.folder.toLowerCase().includes(search))
        .forEach(c => {
            panel.innerHTML += `
            <div class="conversation-item" onclick="openConversation(${c.id})">
                <span>${c.icon}</span>
                <span class="conv-title">${c.title}</span>
            </div>`;
        });
}

async function openConversation(id){
    activeConversationId = id;

    let response = await fetch("/conversation/" + id);
    let data = await response.json();

    document.getElementById("chatbox").innerHTML = "";

    data.messages.forEach(m => {
        if(m.sender === "user"){
            addUserMessage(m.message);
        }else{
            addBotMessage(m.message, m.image, m.file_url, m.preview_url);
        }
    });

    closeSidebarMobile();
}

async function newChat(){
    let response = await fetch("/new_conversation", {method:"POST"});
    let data = await response.json();

    activeConversationId = data.id;

    document.getElementById("chatbox").innerHTML = `
    <div class="empty-state" id="emptyState">
        <h2>New Chat</h2>
        <p>Start a new conversation with Saivex.</p>
    </div>`;

    loadConversations();
    closeSidebarMobile();
}

async function clearHistory(){
    if(!activeConversationId) return;

    await fetch("/delete_conversation/" + activeConversationId, {method:"POST"});

    activeConversationId = null;
    document.getElementById("chatbox").innerHTML = "";
    loadConversations();
}

async function loadMemories(){
    let response = await fetch("/memories");
    let data = await response.json();

    let panel = document.getElementById("memoryPanel");
    panel.innerHTML = "";

    if(data.length === 0){
        panel.innerHTML = `<div class="memory-box"><div class="memory-text">No memories yet.</div></div>`;
        return;
    }

    data.forEach(m => {
        panel.innerHTML += `
        <div class="memory-box">
            <div class="memory-text">${m.value}</div>
            <button class="delete-memory" onclick="deleteMemory(${m.id})">x</button>
        </div>`;
    });
}

async function deleteMemory(id){
    await fetch("/delete_memory/" + id, {method:"POST"});
    loadMemories();
}

async function loadDocuments(){
    let response = await fetch("/documents");
    let data = await response.json();

    let panel = document.getElementById("documentPanel");
    panel.innerHTML = "";

    if(data.length === 0){
        panel.innerHTML = `<div class="document-box"><div class="document-text">No documents.</div></div>`;
        return;
    }

    data.forEach(d => {
        panel.innerHTML += `
        <div class="document-box">
            <div class="document-text">${d.filename}</div>
            <button class="delete-document" onclick="deleteDocument(${d.id})">x</button>
        </div>`;
    });
}

async function deleteDocument(id){
    await fetch("/delete_document/" + id, {method:"POST"});
    loadDocuments();
}

function toolPrompt(type){
    if(type === "ppt") setPrompt("create ppt about ");
    if(type === "pdf") setPrompt("create pdf about ");
    if(type === "website") setPrompt("create website for ");
    if(type === "code") setPrompt("run code: print('Hello from Saivex')");
    if(type === "search") setPrompt("search: ");
    if(type === "vision") setPrompt("explain my uploaded image");
}

document.getElementById("message").addEventListener("keydown", function(e){
    if(e.key === "Enter") sendMessage();
});

loadConversations();
loadMemories();
loadDocuments();
