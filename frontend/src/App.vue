<script setup>
import { computed, nextTick, ref } from 'vue'
import { askQuestion, uploadDocument } from './api'

const documents = ref([])
const messages = ref([])
const question = ref('')
const uploading = ref(false)
const sending = ref(false)
const error = ref('')
const conversation = ref(null)
const readyDocuments = computed(() => documents.value.filter(doc => doc.status === 'ready'))
const suggestions = ['总结这些文档的核心内容', '文档中有哪些重要结论？', '提取文档里的关键数据']

async function scrollToBottom() {
  await nextTick()
  conversation.value.scrollTop = conversation.value.scrollHeight
}

async function uploadFiles(event) {
  const files = Array.from(event.target.files)
  event.target.value = ''
  uploading.value = true
  error.value = ''
  for (const file of files) {
    const doc = { name: file.name, size: file.size, status: 'uploading' }
    documents.value.push(doc)
    const index = documents.value.length - 1
    try {
      const result = await uploadDocument(file)
      documents.value[index] = { ...doc, id: result.id, status: 'ready' }
    } catch (err) {
      documents.value[index].status = 'error'
      error.value = err.message
    }
  }
  uploading.value = false
}

async function sendQuestion(text = question.value) {
  const content = text.trim()
  if (!content || sending.value || !readyDocuments.value.length) return
  const history = messages.value.map(({ role, content }) => ({ role, content }))
  messages.value.push({ role: 'user', content })
  question.value = ''
  sending.value = true
  error.value = ''
  scrollToBottom()
  try {
    const result = await askQuestion(content, readyDocuments.value.map(doc => doc.id), history)
    messages.value.push({ role: 'assistant', content: result.answer, sources: result.sources })
  } catch (err) {
    error.value = err.message
  } finally {
    sending.value = false
    scrollToBottom()
  }
}

function handleEnter(event) {
  if (event.isComposing || event.shiftKey) return
  event.preventDefault()
  sendQuestion()
}

function clearChat() {
  messages.value = []
  error.value = ''
}
</script>

<template>
  <div class="workspace">
    <aside class="sidebar">
      <a class="brand" href="./"><span class="brand-mark">f.</span> folio<span class="brand-tag">知识工作台</span></a>

      <div class="sidebar-heading"><span>我的文档</span><span class="count">{{ readyDocuments.length }}</span></div>
      <p class="sidebar-description">让知识有迹可循，让答案有所依据。</p>

      <label class="upload-zone" :class="{ busy: uploading }">
        <input type="file" multiple :disabled="uploading" @change="uploadFiles" />
        <span class="upload-icon" aria-hidden="true">↑</span>
        <strong>{{ uploading ? '正在上传文档…' : '点击上传文档' }}</strong>
        <span>支持一次选择多个文件</span>
      </label>

      <div v-if="!documents.length" class="documents-empty">还没有文档<br /><span>上传后，就可以开始提问了</span></div>
      <ul v-else class="document-list">
        <li v-for="(doc, index) in documents" :key="index" class="document">
          <span class="file-icon" aria-hidden="true">▤</span>
          <div class="file-info"><strong :title="doc.name">{{ doc.name }}</strong><span>{{ (doc.size / 1024).toFixed(1) }} KB</span></div>
          <span class="file-status" :class="doc.status">{{ { ready: '就绪', uploading: '上传中', error: '失败' }[doc.status] }}</span>
        </li>
      </ul>
      <div class="sidebar-footer"><span class="small-spark">✧</span><div><strong>基于你的文档回答</strong><p>检索相关内容，保留参考来源</p></div></div>
    </aside>

    <main class="main">
      <header class="topbar"><div><span class="status-dot"></span>文档问答<span class="topbar-note">RAG CHAT</span></div><button class="clear-button" :disabled="sending || !messages.length" @click="clearChat">↺ 新对话</button></header>

      <div ref="conversation" class="conversation" aria-live="polite" :aria-busy="sending">
        <section v-if="!messages.length" class="welcome">
          <div class="welcome-icon" aria-hidden="true">✦</div>
          <span class="eyebrow">YOUR DOCUMENTS, CONNECTED.</span>
          <h1>和你的知识，聊一聊。</h1>
          <p>上传文档，提出问题。<br />从散落的信息里，找到有依据的答案。</p>
          <div class="suggestions"><button v-for="suggestion in suggestions" :key="suggestion" :disabled="!readyDocuments.length" @click="sendQuestion(suggestion)"><span>{{ suggestion }}</span><span aria-hidden="true">↗</span></button></div>
          <span class="welcome-hint">{{ readyDocuments.length ? '文档已就绪，试着问一个问题' : '从左侧上传第一份文档，开始探索' }}</span>
        </section>

        <div v-else class="messages">
          <article v-for="(message, index) in messages" :key="index" class="message" :class="message.role">
            <span class="avatar">{{ message.role === 'user' ? '你' : '✦' }}</span>
            <div class="message-body"><span class="message-author">{{ message.role === 'user' ? '你' : 'Folio' }}</span><div class="message-content">{{ message.content }}</div>
              <details v-if="message.sources?.length" class="sources"><summary>参考来源 · {{ message.sources.length }}</summary><div v-for="(source, sourceIndex) in message.sources" :key="sourceIndex" class="source"><strong>{{ sourceIndex + 1 }}. {{ source.name }}</strong><p>{{ source.content }}</p></div></details>
            </div>
          </article>
          <article v-if="sending" class="message assistant"><span class="avatar">✦</span><div class="message-body"><span class="message-author">Folio</span><p class="thinking">正在检索文档并生成回答<span>…</span></p></div></article>
        </div>
      </div>

      <div class="composer-area">
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <form class="composer" @submit.prevent="sendQuestion()">
          <textarea v-model="question" rows="2" aria-label="你的问题" :placeholder="readyDocuments.length ? '关于这些文档，你想了解什么？' : '先上传文档，再开始提问…'" :disabled="sending || !readyDocuments.length" @keydown.enter="handleEnter"></textarea>
          <div class="composer-bottom"><span><span class="context-dot"></span>{{ readyDocuments.length ? `参考 ${readyDocuments.length} 份文档` : '等待上传文档' }}</span><button type="submit" class="send-button" :disabled="sending || !question.trim() || !readyDocuments.length" aria-label="发送问题">↑</button></div>
        </form>
        <p class="composer-hint">Enter 发送 · Shift + Enter 换行<span>回答由 AI 生成，请结合原文核实</span></p>
      </div>
    </main>
  </div>
</template>
