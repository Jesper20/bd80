// Copyright 2023 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { getConfig } from '../utils/config.js';
import { getDjangoError } from '../helpers/fetch.js';

const baseRequest = {
  credentials: 'include',
};

const _getAPI = async uri => {
  const { API_URL } = getConfig();

  let url = `${API_URL}/${uri}`;
  let apiError = { url: url };
  let response, data;

  try {
    response = await fetch(url, {
      method: 'GET',
      ...baseRequest,
    });
    data = await response.clone().json();
  } catch (error) {
    console.error(error);

    apiError.error = error.toString();

    // Based on common reasons for failure cases, make nicer messages

    // Network Errors
    if (error instanceof TypeError && error.message == 'Failed to fetch') {
      apiError.message = `The API didn't respond. Is the API server up?`;

      // Django Errors
    } else if (
      error instanceof SyntaxError &&
      error.message.includes('is not valid JSON')
    ) {
      apiError.message = `The server returned invalid JSON. Is Django returning an error?`;
      apiError.error = `Error: "${response.statusText}"`;
      apiError.extra_error = getDjangoError(await response.text());

      // Fallback Error
    } else {
      apiError.message = `Request encountered an error: ${error.name}`;
    }
    return { apiError };
  }

  // Capture not OK responses
  if (!response?.ok) {
    apiError.message = await response?.text();
    apiError.error = `Server returned ${response?.status} - ${response?.statusText}`;
    return { apiError };
  }

  return data;
};

// video
export const upload = async (userId, payload) => {
// export const upload = async (payload) => {
  const { API_URL } = getConfig();
  let uploadStatus = false;
  let errors;
  console.log(payload)
  // let userId = 2
  // console.log(userId)
  try {
    
    // Retrieve csrf token from server
    const token = await _getAPI('csrf_token');
    //'content-type': 'multipart/form-data',
    //"'Content-Disposition': 'attachment'; filename=upload.jpg
    // 'Content-Disposition': 'attachment', 'filename':'mov.mp4' 
    // Submit form payload and pass back csrf token
    // const response = await fetch(`${API_URL}/upload/`, {
    //const response = await fetch(`${API_URL}/upload/${userId}/`, {
      const response = await fetch(`${API_URL}/uploadvideo/`, {
      // mode:  'no-cors', 
      method: 'POST',
      headers: { 'X-CSRFToken': token.csrfToken, 
          },
      // body: JSON.stringify(payload),
      body: payload,
      ...baseRequest,
    });
    uploadStatus = await response.json();
  } catch (error) {
    errors = [error];
  }
  // if (errors) {
  //   console.error(errors);
  //   uploadStatus = { errors };
  // }
  return uploadStatus;
};

export const doUpload_Fetch = async (userId, payload) => {
  let uri = `products/${userId}/purchase/`;
  const { API_URL } = getConfig();
  console.log(payload)
  let uploadStatus = "no response";
  let url = `${API_URL}/${uri}`;
  try {
    const token = await _getAPI('csrf_token');

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': token.csrfToken },
      body: payload,
      ...baseRequest,
    });
    uploadStatus = await response.json();
    
  } catch (error) {
    console.error(error);
  }
  console.log(uploadStatus)
  return uploadStatus;
};

/////////////////////////////
export const getUser = async uId => {
  return _getAPI(`products/${uId}`);
};

export const getActiveProduct = async () => {
  return _getAPI('active/product/');
};

// export const doUpload = async (userId, callback) => {
//   let uri = `products/${userId}/purchase/`;
//   const { API_URL } = getConfig();

//   let url = `${API_URL}/${uri}`;
//   try {
//     const token = await _getAPI('csrf_token');

//     await fetch(url, {
//       method: 'GET',
//       headers: { 'X-CSRFToken': token.csrfToken },
//       ...baseRequest,
//     });
//     callback && callback(); // callbacks handle error message parsing directly.
//   } catch (error) {
//     console.error(error);
//   }
// };



export const getMessages = async userId => {
  if (userId) {
    return _getAPI(`testimonials/?product_id=${userId}`);
  } else {
    let errorMessage = 'userId required';
    console.log(errorMessage);
    return [{ message: errorMessage }];
  }
};

export const getProductList = async () => {
  return _getAPI(`products/`);
};

export const getSiteConfig = async () => {
  return _getAPI('active/site_config');
};

export const checkout = async payload => {
  const { API_URL } = getConfig();
  let checkoutStatus;
  let errors;

  if (payload?.items?.length) {
    try {
      // Retrieve csrf token from server
      const token = await _getAPI('csrf_token');

      // Submit form payload and pass back csrf token
      const response = await fetch(`${API_URL}/checkout`, {
        method: 'POST',
        headers: { 'X-CSRFToken': token.csrfToken },
        body: JSON.stringify(payload),
        ...baseRequest,
      });
      checkoutStatus = await response.json();
    } catch (error) {
      errors = [error];
    }
  } else {
    errors = [{ message: 'Insufficient information to process checkout.' }];
  }

  if (errors) {
    console.error(errors);
    checkoutStatus = { errors };
  }

  return checkoutStatus;
};
