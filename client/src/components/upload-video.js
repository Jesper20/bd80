// Copyright 2022 Google LLC
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

import { LitElement, html } from 'lit';
import styles from './styles/upload_video.js';
import { doUpload_Fetch, getMessages } from '../utils/fetch.js';
import cache from '../utils/cache.js';
import config from '../utils/config.js';

const noimage = new URL('../../assets/noimage.png', import.meta.url).href;
const oopsAvocado = new URL('../../assets/oops-avocado.png', import.meta.url)
  .href;

let result = { 'msg' : "please upload..." }
let desc = `Your grace, wisdom, and kindness inspire everyone who has the privilege of knowing you. 
You have a way of bringing light and warmth into every room, and your presence is a gift in itself. 
On your special day, may you be surrounded by love, joy, and all the things that make your heart happy. 
May this year bring you endless blessings, cherished memories, and continued success in all that you do. 
Thank you for being a role model, a mentor, and a beacon of positivity. 
You deserve nothing but the very best. Wishing you a beautiful day filled with laughter and a year as amazing as you are!`

export class UploadVideo extends LitElement {
  static get properties() {
    return {
      userId: { type: Number },
      videoItem: { type: Object },
      updateParent: { type: Function },
    };
  }

  static get styles() {
    return styles;
  }

  constructor() {
    super();

    this.state = {
      count: 0,
      openDialog: false,
      openCartDialog: false,
      openSoldOutDialog: false,
      messages: [],
      videoItem: {},
      uploadStatus: "please upload...",
    };

    // Initial default for updateParent
    // Trigger parent components update lifecycle
    this.updateParent = () => {};
  }

  /**
   * Executes when component has initially loaded
   * To read more about lifecycle methods:
   * https://lit.dev/docs/v1/components/lifecycle/#updated
   */
  async updated() {
    let messages = [];
    const { id, inventory_count } = this.videoItem || {};

    // Ensure we are retrieving current video messages
    if (this.state.videoItem?.id !== id) {
      if (id) {
        messages = await getMessages(id);
      }

      this.state = {
        count: inventory_count,
        messages,
      };

      this.state.videoItem = this.videoItem;
      this.requestUpdate();
    }
  }

  /**
   * Toggle the fake video dialog
   */
  toggleDialog() {
    this.state.openDialog = !this.state.openDialog;
    this.requestUpdate();
  }

  /**
   * Toggle the sold out video dialog
   */
  toggleSoldOutDialog() {
    this.state.openSoldOutDialog = !this.state.openSoldOutDialog;
    this.requestUpdate();
  }


  /**
   * Video upload
   */
  // async doUpload_notuse(event) {
  //   event?.preventDefault();
  //   // Disable submit while form is being sent
  //   // this.state.disableSubmit = true;
  //   // this.requestUpdate();

  //   // <input type="file" id="file" accept="video/*"></input><br>
  //   //             <input type="text" id="msg" placeholder="Birthday Message"><br></br>
    
  //   const msg = this.shadowRoot.getElementById('msg').value
  //   // console.log(msg)
  //   const videoFile = this.shadowRoot.getElementById("vfile").files[0]
  //   if(!videoFile) { 
  //     alert('Please select a video file!') 
  //     return
  //   }
  //   // console.log(videoFile)
  //   const video = new FormData()
  //   // const data = new FormData(this.shadowRoot.querySelector('upload') || {});
  //   // FormData.append('video-file', videoFile, 'new-file-name.mp4')
  //   video.append('video', videoFile)
  //   video.append('title', videoFile.name)
  //   // console.log(video)
  //   // video.append('msg', msg)
    
  //   // id = this.videoItem?.id
  //   // await upload(data);
  //   // // Waiting till callstack is empty to re-enable submit button
  //   // setTimeout(() => {
  //   //   this.state.disableSubmit = false;
  //   //   this.requestUpdate();
  //   // }, 0);
  //   // if (this.state.count < 100000) {
    
  //   // use following code
  //   // await upload(videoFile, () => {
  //   await upload(this.videoItem?.id, video, () => {
  //     this.state.count++;
  //     // Open fake video dialog
  //     this.toggleDialog();
  //   });
  //   // } else {
  //   //   // Open reach target dialog
  //   //   this.toggleSoldOutDialog();
  //   // }
  // }
  
  async doUpload(event) {
    event?.preventDefault();
    result = {'msg' : "Uploading..."}
    const videoFile = this.shadowRoot.getElementById("vfile").files[0]
    const video = new FormData()
    video.append('video', videoFile)
    video.append('title', videoFile.name)

    if (this.state.count < 1000000) {
      result = await doUpload_Fetch(this.videoItem?.id, video, () => {
        this.state.count++;
        // Open fake video dialog
        this.toggleDialog();
      });
      // await handle_response(resp)
      // document.getElementById("uploadstatus").innerText = resp
      this.state.uploadStatus = await result
     
    } else {
      // Open sold out dialog
      this.toggleSoldOutDialog();
    }
    this.requestUpdate();
  }


  render() {
    // const { AVOCANO_PURCHASE_MODE } = config.getConfig();
    const {
      count,
      messages,
      openDialog,
      openCartDialog,
      openSoldOutDialog,
    } = this.state;

    const {
      name,
      image,
      description,
    } = this.videoItem || {};

    return html`
      <div class="videoItemContainer">
        <div class="videoItemWrapper">
          <div class="videoimageWrapper">
            <img
              class="videoimage"
              alt="video logo"
              src=${image}
              loading="lazy"
              onerror=${`this.src='${noimage}';`}
            />
          </div>

         <div class="videoItemContent">
            <h2 class="itemTitle">💜 ${name} 💜 </h2>

            <div class="inventory" style="margin:auto;">
              ${count < 1000000 ? `${count} videos so far!` : `We have reached the target!`}
            </div>
            <div>
              <form id="upload" class="upload">
                <label for="vfile"></label>
                <input class="fileUpload" type="file" id="vfile" accept="video/*" placeholder="Please choose your video"></input><br><br>
                <!-- <input type="text" id="msg" placeholder="Birthday Message"><br> -->
                <a href="#" class="buyButton" label="Buy" @click="${this.doUpload}">Upload Video</a><br><br>
              </form>
            </div>
            <div id="uploadstatus" class="result">${JSON.stringify(result)}</div><br><br>
          </div>
          
         
        </div>
        <div class="videoDescription">${desc}</div>
        <!-- <div class="messagesWrapper">
          <div class="messagesHeader">
            <h3>messages</h3>
          </div>
          <div class="messagesContent">
            ${messages?.length
              ? messages.map(
                  (item) => html`
                    <div class="messagesItem">
                      <div class="testimonialItemContent">
                        <div class="rating">
                          ${`★`.repeat(item.rating)}${`☆`.repeat(
                            5 - item.rating,
                          )}
                        </div>
                        <div class="reviewerDetails">
                          ${item.reviewer_name} from ${item.reviewer_location}
                        </div>
                        <div class="reviewSummary">${item.summary}</div>
                        <div class="reviewDescription">${item.description}</div>
                      </div>
                    </div>
                  `,
                )
              : html`<p>No messages ... yet</p>`}
          </div>
        </div> -->
       
      </div>
    `;
  }
}

customElements.define('app-upload-video', UploadVideo);
