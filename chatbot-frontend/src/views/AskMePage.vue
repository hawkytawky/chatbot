<script>
import axios from 'axios';

const backend_url = 'http://127.0.0.1:8000'

export default {
  data() {
    return {
      userInput: '',
      response: '', 
      messages: [],
      chat_history: [],
      isLoading_load: false,
      isLoading_button: true,
      showModal: true,
    };
  },
  
  methods: {

    adjustTextareaHeight(event) {
      const textarea = event.target;
      textarea.style.height = 'auto'; 
      textarea.style.height = textarea.scrollHeight + 'px'; 
    },

    addMessageToHistory(sender, text) {
      this.chat_history.push( {sender, text});
    },

    handleClick() {
      if (this.userInput.trim().length > 0) {
        this.isLoading_button = false;
        this.isLoading_load = true;
        this.addMessageToHistory('user', this.userInput);

        const ask_url = `${backend_url}/ask` // ask endpoint in backend

        axios.post(ask_url, { 
          user_input: this.userInput,
          chat_history: this.chat_history
          })
          .then(response => {
            this.addMessageToHistory('bot', response.data)
            this.response = response.data;

            this.messages.push({ 
              id: Date.now(), 
              text: this.userInput, 
              sender: 'user'});
            this.messages.push({ 
              id: Date.now() + 1, 
              text: this.response, 
              sender: 'bot'});

            this.userInput = '';
            this.isLoading_load = false;
            this.isLoading_button = true;
            this.scrollToBottom();
          })
          .catch(error => {
            console.error('Error: ', error);
          });
      } else {
        this.response = "OOPS, you forgot to send something. Try again! :)"; 
        this.messages.push({ id: Date.now(), text: this.response, sender: 'bot'});
        this.scrollToBottom();
      }
    },

    closeModal() {
      this.showModal = false;
    },

    scrollToBottom() {
      this.$nextTick(() => {
        setTimeout(() => {
          const chatContainer = this.$refs.chatContainer;
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 50);
      });
    },
  },

  mounted() {
    this.$nextTick(() => {
      const textarea = this.$refs.textarea;
      if (textarea) {
        this.adjustTextareaHeight({ target: textarea });
      }
    });
  }
}
</script>

<template>
  <div class="container">
    <!-- Modal -->
    <div v-if="showModal" class="modal">
    <div class="modal-content">
        <div class="modal-text">
            <h2>Welcome to my personal chatbot! 👋🏻</h2>
            <p>Here you can ask me any personal questions about my life, for example:</p>
            <div class="custom-list">
              <div class="custom-list-item">- Tell me about your previous working experience 🧑🏼‍💻</div>
              <div class="custom-list-item">- Tell me more about your bachelor or master thesis 📚</div>
              <div class="custom-list-item">- Tell me more about your experience in SAP in Singapore 🇸🇬</div>
              <div class="custom-list-item">- Tell me something about you that I cannot see from your CV 🌍</div>
            </div>
            <p> Looking forward to have a chat with you 😎</p>
            <button @click="closeModal">Let's go!</button>
        </div>
        <img src="/xd.jpg" alt="Your Image" class="modal-image">
    </div>
    </div>


    <div class ="input-area">
      <div class="input-container">
        <textarea 
          v-model="userInput"
          placeholder="Ask Me Anything" 
          @input="adjustTextareaHeight"
          @keyup.enter="handleClick"
          @keydown.enter.prevent="handleEnterPress"
          ref="textarea">
        </textarea>
      </div>

      <!-- Loading Icon -->
      <img src="@/assets/ring.gif" 
      alt="Loading" 
      v-show="isLoading_load" 
      class="loading-icon" />

      <!-- Submit Button -->
      <img class="submit-button"
      src="@/assets/button.png" 
      alt="Submit" 
      @click="handleClick"
      v-show="isLoading_button"/>

    </div>

      <div class="chat-container" ref="chatContainer">
        <div v-for="message in messages" :key="message.id" class="chat-message" >
          <span :class="{'user-message': message.sender === 'user', 'bot-message': message.sender === 'bot', 'justified': message.sender === 'bot'}">
            {{ message.text }}
          </span>
        </div>
      </div>

  </div>

</template>


<style>
/* APP LAYER */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow-x: hidden;
  overflow-y: hidden;
}

#app {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%; 
  width: 100%;
  overflow-x: hidden;
  overflow-y: hidden;
}

/* CONTAINER LAYER */
.container {
  height: 100%;
  width: 70%;
  justify-content: flex-start;
  align-items: center;
}

/* INPUT AREA */
.input-area {
  position: fixed;
  display: flex;
  width: 70%;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

/* INPUT CONTAINER LAYER */
.input-container {
  display: flex;
  justify-content: center;
  left: 20%;
  border: 2px solid #182424;
  border-radius: 4px;
  padding: 0; 
  flex-grow: 1;
  margin-top: 0 !important;
}

/* INPUT CONTAINER TEXTAREA */
.input-container textarea {
  vertical-align: middle;
  line-height: 1.5;
  width: 100%;
  min-height: 100%;
  max-height: 35px;
  border: none;
  outline: none;
  padding: 5px;
  font-size: 17px;
  resize: none;
  box-sizing: border-box;
  flex-grow: 1
}

/* RESPONSE BOX */
.response-box {
  display: flex;
  border: 2px solid rgba(24,36,36,1); 
  border-radius: 4px;
  background-color: rgba(24,36,36,1); 
  color: rgba(249,247,240,255); 
  padding: 10px; 
  margin: 20px;
}

/* OUTPUT CONTAINER */
.output-container {
  display: relative;
}

/* CHAT CONTAINER */
.chat-container {
  display: fixed;
  flex-direction: column;
  overflow-y: auto;
  align-items: flex-start;
  width: 100%;
  margin-top: 50px;
  max-height: 75%;
  background-color: rgba(249,247,240,255);
  flex-grow: 1;
}

.chat-message {
  display: flex;
  margin-bottom: 10px;
  padding: 5px;
  border-radius: 5px;
  width: 100%;
}

.user-message {
  text-align: left;
  background-color: #e0f0e3;
  color: rgb(78, 77, 77);
  margin-right: 5%;
  border-radius: 4px;
  padding: 5px;
  max-width: 88%; 
}

.bot-message {
  text-align: right;
  background-color: #d8e1e8;
  color: rgb(78, 77, 77);
  margin-left: auto; 
  border-radius: 4px;
  padding: 5px;
  margin-right: 5%;
  max-width: 88%; 
}

/* BLOCKSATZ */
.justified {
  text-align: justify;
}

/* BUTTON */
.submit-button {
  position: relative; 
  margin-left: 5px;
  cursor: pointer;
  width: 38px;
  height: 38px;
}

/* LOADING ICON */
.loading-icon {
  position: relative;
  margin-left: 5px;
  height: 40px;
  margin-top: 0 !important;
}

* {
  box-sizing: border-box;
}

/* Popup */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: flex-start; 
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  padding-top: 50px; 
}

.modal-content {
  background-color: white;
  padding: 12px;
  border-radius: 5px;
  display: flex;
  align-items: center; 
  justify-content: space-between; 
  width: 70%;
}

.custom-list {
  display: inline-block; 
  text-align: left; 
  margin: 0; 
  margin-left: 100px;
}

.modal-text {
  justify-content: center; 
  align-items: left; 
  flex-direction: column; 
  margin-left: 60px;
  text-align: left; 
  width: 80%;
}

.modal-text p {
  margin-bottom: 5px;
  margin-top: 5px;
  align-items: left;
  margin-left: 60px !important;
}

.modal-text h2 {
  padding: 10px;
  margin: 0;
  text-align: center;
}

.custom-list-item {
    margin-bottom: 1px; 
    margin-left: 0px;
}

.modal-image {
  width: 100px; 
  height: auto;
  margin-right: 60px;
}

.close {
  color: #aaa;
  float: right;
  font-size: 28px;
  font-weight: bold;
}

.close:hover,
.close:focus {
  color: black;
  text-decoration: none;
  cursor: pointer;
}

.modal-text button{
  margin-top:14px;
  margin-left: 42%;
}

</style>