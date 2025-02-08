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
import { getActiveProduct } from '../utils/fetch.js';
import cache from '../utils/cache.js';
import styles from './styles/home.js';
import '../components/upload-video.js';

export class Home extends LitElement {
  constructor() {
    super();
    this.title = 'Home';
    this.state = {
      status: 'loading',
      videoItem: {},
    };
  }

  static get styles() {
    return styles;
  }

  async disconnectedCallback() {
    super.disconnectedCallback();
    cache.deleteDB();
  }

  async firstUpdated() {
    const videoItem = await getActiveProduct();

    this.state = {
      ...this.state,
      status: 'loaded',
      videoItem,
    };

    if (videoItem?.apiError) {
      this.state.apiError = videoItem.apiError;
    }

    this.requestUpdate();
  }

  render() {
    const { status, videoItem, apiError } = this.state;

    if (apiError) {
      return html`<div class="homeBase">
        <p>No active product found. Check <a href="/products">Products</a>.</p>
      </div>`;
    }

    return html`
      <div class="homeBase">
        ${status === 'loading'
          ? html`<p class="loading">loading... 🥑</p>`
          : html`

          <h1>Join us in celebrating this special day 
          by sending your heartfelt birthday wish video</h1>
          
          <app-upload-video
              .userId="${this.userId}"
              .videoItem=${videoItem}
            ></app-upload-video>`}
      </div>
    `;
  }
}

customElements.define('app-home', Home);
