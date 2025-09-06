const axios = require('axios');

async function getToken() {
  try {
    const response = await axios.post('http://127.0.0.1:5001/api/auth/login', {
      username: 'admin',
      password: 'admin123'
    }, {
      headers: {
        'Host': 'default.localhost'
      }
    });
    if (response.data.success) {
      console.log(response.data.data.access_token);
    } else {
      console.error('Failed to get token:', response.data.message);
    }
  } catch (error) {
    console.error('Error getting token:', error.response?.data || error.message);
  }
}

getToken();