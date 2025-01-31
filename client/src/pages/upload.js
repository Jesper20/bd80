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
import { getUser } from '../utils/fetch.js';
import styles from './styles/upload.js';

import '../components/upload-video.js';

export class Upload extends LitElement {
  static get properties() {
    return {
      userId: { type: Number },
      updateParent: { type: Function },
    };
  }

  static get styles() {
    return styles;
  }

  constructor() {
    super();
    this.state = {
      status: 'loading',
      user: {},
    };

    // Initial value for updateParent
    // Trigger parent components update lifecycle
    this.updateParent = () => {};
  }

  async updated() {
    const prevItem = this.state.user;
    let user;

    // Fetch user ID
    if (this.userId) {
      user = await getUser(this.userId);

      this.state = {
        ...this.state,
        status: 'loaded',
        user,
      };

      // If there was an error, make sure this is captured.
      if (user?.apiError) {
        this.state.apiError = user.apiError;
        this.requestUpdate(); // BUG(glasnt): with this, the page API loops. Without, it doesn't update at all.
      }
      // Only update if the previously loaded product
      // is different than the requested product
      if (prevItem?.id !== this.userId) {
        this.requestUpdate();
      }
    }
  }

  render() {
    const { status, user, apiError } = this.state;

    if (apiError) {
      return html`<app-error .apiError=${apiError}></app-error>`;
    }

    return html`
      <div class="productBase">
        ${status === 'loading'
          ? html`<p>loading...</p>`
          : html`<app-upload-video
              .userId="{this.userId}"
              .user=${user}
              .updateParent=${this.updateParent}
            ></<app-upload-video>`}
      </div>
    `;
  }
}

customElements.define('app-upload', Upload);
