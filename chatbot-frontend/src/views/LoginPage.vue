<script>
import axios from 'axios';

const backend_url = 'http://127.0.0.1:8000'

export default {
  data() {
    return {
      userInput: '',
      responseMessage: '',
      isAuthenticated: false,
      isLoading: false,
    };
  },
  methods: {
    handleClick() {
      if (this.userInput.trim()) {
        this.isLoading = true;
        const login_url = `${backend_url}/login`; 

        axios.post(login_url, { password: this.userInput })
          .then(response => {
            this.responseMessage = response.data.message;
            this.isAuthenticated = true;
            // to askmepage
            localStorage.setItem('userIsAuthenticated', 'true');
            this.$router.push({ name: 'AskMePage' });
          })
          .catch(error => {
            this.responseMessage = error.response && error.response.status === 401 
                                  ? "Wrong Password!" 
                                  : "Error, wrong password!";
            this.isAuthenticated = false;
          })
          .finally(() => {
            this.isLoading = false;
          });
      } else {
        this.responseMessage = "Please enter a password";
      }
    },
  },
}
</script>

<template>
  <div class="login-container">
    <input 
      type="password" 
      @keyup.enter="handleClick" 
      v-model="userInput" 
      placeholder="Enter password" :disabled="isLoading" />
    <button 
      @click="handleClick" :disabled="isLoading">Login</button>
    <p v-if="responseMessage">{{ responseMessage }}</p>
  </div>
</template>

<style>
.login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start; 
  height: 100vh; 
  padding-top: 20vh;
  width: 60vh;
}

.login-container input, .login-container button {
  margin: 10px 0;
  height: 6%;
  width: 60%;
  border: 1px solid rgba(24, 36, 36, 1);
  border-radius: 4px;
  font-size: 15px;
}

.loading-icon {
  margin-top: 20px; 
}
</style>

