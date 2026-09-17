<template>
  <div class="home-container">
    <!-- 动态背景纹理 -->
    <div class="bg-texture">
      <div class="bg-noise"></div>
      <div class="bg-orb orb-1"></div>
      <div class="bg-orb orb-2"></div>
      <div class="bg-orb orb-3"></div>
    </div>

    <!-- 页面头部 -->
    <div class="hero-section">
      <div class="hero-badge">
        <span class="badge-dot"></span>
        <span class="badge-text">AI 智能规划</span>
      </div>
      <h1 class="hero-title">
        <span class="title-line">发现你的</span>
        <span class="title-line title-accent">下一段旅程</span>
      </h1>
      <p class="hero-desc">
        输入目的地与偏好，让 AI 为你量身定制独一无二的旅行方案
      </p>
    </div>

    <!-- 表单卡片 -->
    <a-card class="form-card" :bordered="false">
      <a-form :model="formData" layout="vertical" @finish="handleSubmit">

        <!-- 目的地与日期 -->
        <div class="form-section">
          <div class="section-header">
            <div class="section-number">01</div>
            <div class="section-meta">
              <h3 class="section-title">目的地与日期</h3>
              <p class="section-subtitle">选择你想探索的城市和时间</p>
            </div>
          </div>

          <a-row :gutter="24">
            <a-col :xs="24" :sm="24" :md="8">
              <a-form-item name="city" :rules="[{ required: true, message: '请输入目的地城市' }]">
                <template #label>
                  <span class="form-label">目的地城市</span>
                </template>
                <a-input
                  v-model:value="formData.city"
                  placeholder="例如：北京、上海、东京..."
                  size="large"
                  class="custom-input"
                >
                  <template #prefix>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="input-icon">
                      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                      <circle cx="12" cy="10" r="3"/>
                    </svg>
                  </template>
                </a-input>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="12" :md="6">
              <a-form-item name="start_date" :rules="[{ required: true, message: '请选择开始日期' }]">
                <template #label>
                  <span class="form-label">开始日期</span>
                </template>
                <a-date-picker
                  v-model:value="formData.start_date"
                  style="width: 100%"
                  size="large"
                  class="custom-input"
                  placeholder="选择日期"
                />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="12" :md="6">
              <a-form-item name="end_date" :rules="[{ required: true, message: '请选择结束日期' }]">
                <template #label>
                  <span class="form-label">结束日期</span>
                </template>
                <a-date-picker
                  v-model:value="formData.end_date"
                  style="width: 100%"
                  size="large"
                  class="custom-input"
                  placeholder="选择日期"
                />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="24" :md="4">
              <a-form-item>
                <template #label>
                  <span class="form-label">旅行天数</span>
                </template>
                <div class="days-pill">
                  <span class="days-value">{{ formData.travel_days }}</span>
                  <span class="days-unit">天</span>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 偏好设置 -->
        <div class="form-section">
          <div class="section-header">
            <div class="section-number">02</div>
            <div class="section-meta">
              <h3 class="section-title">偏好设置</h3>
              <p class="section-subtitle">告诉我们你的旅行风格</p>
            </div>
          </div>

          <a-row :gutter="24">
            <a-col :xs="24" :sm="12" :md="8">
              <a-form-item name="transportation">
                <template #label>
                  <span class="form-label">交通方式</span>
                </template>
                <a-select v-model:value="formData.transportation" size="large" class="custom-select">
                  <a-select-option value="公共交通">公共交通</a-select-option>
                  <a-select-option value="自驾">自驾</a-select-option>
                  <a-select-option value="步行">步行</a-select-option>
                  <a-select-option value="混合">混合出行</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="12" :md="8">
              <a-form-item name="accommodation">
                <template #label>
                  <span class="form-label">住宿偏好</span>
                </template>
                <a-select v-model:value="formData.accommodation" size="large" class="custom-select">
                  <a-select-option value="经济型酒店">经济型酒店</a-select-option>
                  <a-select-option value="舒适型酒店">舒适型酒店</a-select-option>
                  <a-select-option value="豪华酒店">豪华酒店</a-select-option>
                  <a-select-option value="民宿">民宿</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="24" :md="8">
              <a-form-item name="preferences">
                <template #label>
                  <span class="form-label">旅行偏好</span>
                </template>
                <div class="preference-chips">
                  <a-checkbox-group v-model:value="formData.preferences" class="custom-checkbox-group">
                    <a-checkbox value="历史文化" class="preference-chip">历史文化</a-checkbox>
                    <a-checkbox value="自然风光" class="preference-chip">自然风光</a-checkbox>
                    <a-checkbox value="美食" class="preference-chip">美食</a-checkbox>
                    <a-checkbox value="购物" class="preference-chip">购物</a-checkbox>
                    <a-checkbox value="艺术" class="preference-chip">艺术</a-checkbox>
                    <a-checkbox value="休闲" class="preference-chip">休闲</a-checkbox>
                  </a-checkbox-group>
                </div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>

        <!-- 可验证约束 -->
        <div class="form-section">
          <div class="section-header">
            <div class="section-number">03</div>
            <div class="section-meta">
              <h3 class="section-title">约束与个人资料</h3>
              <p class="section-subtitle">预算和资料会进入校验与证据检索链路</p>
            </div>
          </div>

          <a-row :gutter="24">
            <a-col :xs="24" :sm="12" :md="6">
              <a-form-item label="总预算上限">
                <a-input-number v-model:value="formData.max_budget" :min="0" :step="100" placeholder="不限制" style="width: 100%" size="large" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :sm="12" :md="6">
              <a-form-item label="每日最多景点">
                <a-input-number v-model:value="formData.max_daily_attractions" :min="1" :max="6" style="width: 100%" size="large" />
              </a-form-item>
            </a-col>
            <a-col :xs="24" :md="12">
              <a-form-item label="特殊约束">
                <a-select v-model:value="formData.accessibility_needs" mode="tags" placeholder="如：轮椅通行、儿童推车、海鲜过敏" size="large" />
              </a-form-item>
            </a-col>
          </a-row>

          <div class="knowledge-upload">
            <label class="upload-label">
              <span>{{ uploadingMaterial ? '正在解析资料…' : '上传攻略、订单、票据或旅行截图' }}</span>
              <input type="file" accept=".txt,.md,.json,.csv,.pdf,.png,.jpg,.jpeg,.webp" :disabled="uploadingMaterial" @change="handleMaterialUpload" />
            </label>
            <div v-if="uploadedMaterials.length" class="uploaded-list">
              <span v-for="item in uploadedMaterials" :key="item.sourceId" class="material-chip">✓ {{ item.name }} · {{ item.chunks }} chunks</span>
            </div>
          </div>
          <a-checkbox v-model:checked="formData.enable_experience_learning" class="learning-consent">
            授权保存脱敏后的完整规划样本，用于难例挖掘和版本回归
          </a-checkbox>
        </div>

        <!-- 额外要求 -->
        <div class="form-section">
          <div class="section-header">
            <div class="section-number">04</div>
            <div class="section-meta">
              <h3 class="section-title">额外要求</h3>
              <p class="section-subtitle">补充任何特殊需求或想法</p>
            </div>
          </div>

          <a-form-item name="free_text_input">
            <a-textarea
              v-model:value="formData.free_text_input"
              placeholder="例如：想去看升旗、需要无障碍设施、对海鲜过敏、希望包含亲子活动..."
              :rows="4"
              size="large"
              class="custom-textarea"
            />
          </a-form-item>
        </div>

        <!-- 提交 -->
        <a-form-item>
          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="!loading" class="btn-content">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polygon points="10 8 16 12 10 16 10 8"/>
              </svg>
              <span>开始规划行程</span>
            </span>
            <span v-else class="btn-content">
              <span class="btn-spinner"></span>
              <span>正在生成中...</span>
            </span>
          </button>
        </a-form-item>

        <!-- 加载进度 -->
        <a-form-item v-if="loading">
          <div class="loading-panel">
            <a-progress
              :percent="loadingProgress"
              status="active"
              :stroke-color="{ '0%': '#0f3460', '100%': '#e94560' }"
              :stroke-width="8"
              :show-info="false"
            />
            <p class="loading-status">{{ loadingStatus }}</p>
          </div>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 底部装饰 -->
    <div class="home-footer">
      <div class="footer-stats">
        <div class="stat-item">
          <span class="stat-value">∞</span>
          <span class="stat-label">目的地覆盖</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">AI</span>
          <span class="stat-label">智能规划</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">实时</span>
          <span class="stat-label">信息更新</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { generateTripPlan, uploadKnowledge } from '@/services/api'
import { createWorkspaceRun } from '@/services/workspace'
import type { TripFormData } from '@/types'
import type { Dayjs } from 'dayjs'

const router = useRouter()
const loading = ref(false)
const loadingProgress = ref(0)
const loadingStatus = ref('')

interface HomeFormData {
  city: string
  start_date: Dayjs | null
  end_date: Dayjs | null
  travel_days: number
  transportation: string
  accommodation: string
  preferences: string[]
  free_text_input: string
  max_budget?: number
  max_daily_attractions: number
  accessibility_needs: string[]
  knowledge_source_ids: string[]
  enable_experience_learning: boolean
}

const formData = reactive<HomeFormData>({
  city: '',
  start_date: null,
  end_date: null,
  travel_days: 1,
  transportation: '公共交通',
  accommodation: '经济型酒店',
  preferences: [],
  free_text_input: '',
  max_budget: undefined,
  max_daily_attractions: 3,
  accessibility_needs: [],
  knowledge_source_ids: [],
  enable_experience_learning: false
})

const uploadingMaterial = ref(false)
const uploadedMaterials = ref<Array<{ sourceId: string; name: string; chunks: number }>>([])

const handleMaterialUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  uploadingMaterial.value = true
  try {
    const result = await uploadKnowledge(file)
    formData.knowledge_source_ids.push(result.source_id)
    uploadedMaterials.value.push({ sourceId: result.source_id, name: result.source_name, chunks: result.chunks })
    message.success(`资料解析完成，共生成 ${result.chunks} 个检索片段`)
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '资料解析失败')
  } finally {
    uploadingMaterial.value = false
    input.value = ''
  }
}

watch([() => formData.start_date, () => formData.end_date], ([start, end]) => {
  if (start && end) {
    const days = end.diff(start, 'day') + 1
    if (days > 0 && days <= 30) {
      formData.travel_days = days
    } else if (days > 30) {
      message.warning('旅行天数不能超过30天')
      formData.end_date = null
    } else {
      message.warning('结束日期不能早于开始日期')
      formData.end_date = null
    }
  }
})

const handleSubmit = async () => {
  if (!formData.start_date || !formData.end_date) {
    message.error('请选择日期')
    return
  }

  loading.value = true
  loadingProgress.value = 0
  loadingStatus.value = '正在初始化...'

  const progressInterval = setInterval(() => {
    if (loadingProgress.value < 90) {
      loadingProgress.value += Math.floor(Math.random() * 8) + 3
      if (loadingProgress.value > 90) loadingProgress.value = 90

      if (loadingProgress.value <= 30) {
        loadingStatus.value = '正在搜索热门景点...'
      } else if (loadingProgress.value <= 50) {
        loadingStatus.value = '分析天气与交通...'
      } else if (loadingProgress.value <= 70) {
        loadingStatus.value = '匹配住宿与餐饮...'
      } else {
        loadingStatus.value = '生成完整行程...'
      }
    }
  }, 600)

  try {
    const requestData: TripFormData = {
      city: formData.city,
      start_date: formData.start_date.format('YYYY-MM-DD'),
      end_date: formData.end_date.format('YYYY-MM-DD'),
      travel_days: formData.travel_days,
      transportation: formData.transportation,
      accommodation: formData.accommodation,
      preferences: formData.preferences,
      free_text_input: formData.free_text_input,
      max_budget: formData.max_budget,
      max_daily_attractions: formData.max_daily_attractions,
      accessibility_needs: formData.accessibility_needs,
      knowledge_source_ids: formData.knowledge_source_ids,
      enable_experience_learning: formData.enable_experience_learning
    }

    const response = await generateTripPlan(requestData)

    clearInterval(progressInterval)
    loadingProgress.value = 100
    loadingStatus.value = '行程规划完成！'

    if (response.success && response.data) {
      sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
      sessionStorage.setItem('tripRequest', JSON.stringify(requestData))
      createWorkspaceRun(requestData, response.data)
      message.success('旅行计划生成成功！')
      setTimeout(() => {
        router.push('/result')
      }, 500)
    } else {
      message.error(response.message || '生成失败')
    }
  } catch (error: any) {
    clearInterval(progressInterval)
    message.error(error.message || '生成旅行计划失败，请稍后重试')
  } finally {
    setTimeout(() => {
      loading.value = false
      loadingProgress.value = 0
      loadingStatus.value = ''
    }, 1200)
  }
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: var(--color-cream);
  padding: 60px 24px 80px;
  position: relative;
  overflow: hidden;
}

.knowledge-upload {
  padding: 18px;
  border: 1px dashed rgba(15, 52, 96, 0.35);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.55);
}

.upload-label {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  color: #0f3460;
  font-weight: 600;
  cursor: pointer;
}

.upload-label input {
  display: none;
}

.uploaded-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.learning-consent {
  margin-top: 14px;
  color: #595959;
}

.material-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(15, 52, 96, 0.08);
  color: #0f3460;
  font-size: 12px;
}

/* 背景纹理 */
.bg-texture {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.bg-noise {
  position: absolute;
  inset: 0;
  opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 256px 256px;
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;
}

.orb-1 {
  width: 500px;
  height: 500px;
  top: -200px;
  right: -100px;
  background: #e94560;
  animation: drift 20s infinite ease-in-out;
}

.orb-2 {
  width: 400px;
  height: 400px;
  bottom: 10%;
  left: -150px;
  background: #0f3460;
  animation: drift 25s infinite ease-in-out reverse;
}

.orb-3 {
  width: 300px;
  height: 300px;
  top: 40%;
  right: 10%;
  background: #16213e;
  animation: drift 18s infinite ease-in-out;
  animation-delay: -5s;
}

@keyframes drift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

/* Hero 区域 */
.hero-section {
  text-align: center;
  margin-bottom: 48px;
  position: relative;
  z-index: 1;
  animation: fadeInDown 0.8s ease-out;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(233, 69, 96, 0.08);
  border: 1px solid rgba(233, 69, 96, 0.2);
  border-radius: 100px;
  margin-bottom: 20px;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-warm);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.badge-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-warm);
  letter-spacing: 0.5px;
}

.hero-title {
  font-family: var(--font-display);
  margin: 0 0 16px;
  line-height: 1.2;
}

.title-line {
  display: block;
  font-size: 48px;
  font-weight: 700;
  color: var(--color-ink);
  letter-spacing: 2px;
}

.title-accent {
  color: var(--color-warm);
  position: relative;
}

.title-accent::after {
  content: '';
  position: absolute;
  bottom: 4px;
  left: 0;
  width: 100%;
  height: 8px;
  background: rgba(233, 69, 96, 0.15);
  border-radius: 4px;
  z-index: -1;
}

.hero-desc {
  font-size: 16px;
  color: var(--color-muted);
  max-width: 480px;
  margin: 0 auto;
  line-height: 1.6;
  font-weight: 400;
}

/* 表单卡片 */
.form-card {
  max-width: 1100px;
  margin: 0 auto;
  border-radius: 20px;
  box-shadow: 0 1px 3px rgba(26, 26, 46, 0.04), 0 12px 40px rgba(26, 26, 46, 0.06);
  position: relative;
  z-index: 1;
  background: var(--color-paper) !important;
  animation: fadeInUp 0.8s ease-out;
  border: 1px solid var(--color-border);
}

/* 表单分区 */
.form-section {
  margin-bottom: 36px;
  padding: 32px;
  background: var(--color-cream);
  border-radius: 16px;
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
}

.form-section:hover {
  box-shadow: 0 4px 20px rgba(15, 52, 96, 0.06);
  border-color: rgba(15, 52, 96, 0.12);
}

.section-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.section-number {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-ink);
  color: white;
  font-size: 14px;
  font-weight: 700;
  border-radius: 10px;
  flex-shrink: 0;
}

.section-meta {
  flex: 1;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-ink);
  margin: 0 0 4px;
}

.section-subtitle {
  font-size: 13px;
  color: var(--color-muted);
  margin: 0;
}

/* 表单标签 */
.form-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-slate);
}

/* 自定义输入框 */
.custom-input :deep(.ant-input),
.custom-input :deep(.ant-picker) {
  border-radius: 10px;
  border: 1.5px solid var(--color-border);
  background: var(--color-paper);
  transition: all 0.25s ease;
  font-size: 14px;
}

.custom-input :deep(.ant-input:hover),
.custom-input :deep(.ant-picker:hover) {
  border-color: var(--color-accent);
}

.custom-input :deep(.ant-input:focus),
.custom-input :deep(.ant-picker-focused) {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(15, 52, 96, 0.08);
}

.input-icon {
  color: var(--color-muted);
  margin-right: 4px;
}

/* 自定义选择框 */
.custom-select :deep(.ant-select-selector) {
  border-radius: 10px !important;
  border: 1.5px solid var(--color-border) !important;
  background: var(--color-paper) !important;
  transition: all 0.25s ease !important;
}

.custom-select:hover :deep(.ant-select-selector) {
  border-color: var(--color-accent) !important;
}

.custom-select :deep(.ant-select-focused .ant-select-selector) {
  border-color: var(--color-accent) !important;
  box-shadow: 0 0 0 3px rgba(15, 52, 96, 0.08) !important;
}

/* 天数显示 */
.days-pill {
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  padding: 8px 20px;
  background: var(--color-ink);
  border-radius: 10px;
  color: white;
}

.days-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}

.days-unit {
  font-size: 14px;
  font-weight: 500;
  opacity: 0.8;
}

/* 偏好标签 */
.preference-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.custom-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.preference-chip :deep(.ant-checkbox-wrapper) {
  margin: 0 !important;
  padding: 8px 14px;
  border: 1.5px solid var(--color-border);
  border-radius: 10px;
  transition: all 0.25s ease;
  background: var(--color-paper);
  font-size: 13px;
  color: var(--color-slate);
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.preference-chip :deep(.ant-checkbox-wrapper:hover) {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.preference-chip :deep(.ant-checkbox-wrapper-checked) {
  border-color: var(--color-warm);
  background: var(--color-warm);
  color: white;
}

.preference-chip :deep(.ant-checkbox-wrapper-checked .ant-checkbox-inner) {
  background-color: white;
  border-color: white;
}

.preference-chip :deep(.ant-checkbox-wrapper-checked .ant-checkbox-inner::after) {
  border-color: var(--color-warm);
}

.preference-chip :deep(.ant-checkbox) {
  top: 0;
}

.preference-chip :deep(.ant-checkbox + span) {
  padding: 0;
}

/* 文本域 */
.custom-textarea :deep(.ant-input) {
  border-radius: 10px;
  border: 1.5px solid var(--color-border);
  background: var(--color-paper);
  transition: all 0.25s ease;
  font-size: 14px;
  resize: vertical;
}

.custom-textarea :deep(.ant-input:hover) {
  border-color: var(--color-accent);
}

.custom-textarea :deep(.ant-input:focus) {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px rgba(15, 52, 96, 0.08);
}

/* 提交按钮 */
.submit-btn {
  width: 100%;
  height: 56px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: var(--color-ink);
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  letter-spacing: 0.5px;
}

.submit-btn:hover:not(:disabled) {
  background: var(--color-slate);
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(26, 26, 46, 0.2);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.btn-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 加载面板 */
.loading-panel {
  text-align: center;
  padding: 28px;
  background: var(--color-cream);
  border-radius: 12px;
  border: 1px dashed var(--color-border);
}

.loading-status {
  margin-top: 14px;
  color: var(--color-accent);
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

/* 底部统计 */
.home-footer {
  max-width: 1100px;
  margin: 48px auto 0;
  position: relative;
  z-index: 1;
  animation: fadeInUp 0.8s ease-out 0.2s both;
}

.footer-stats {
  display: flex;
  justify-content: center;
  gap: 48px;
  padding-top: 32px;
  border-top: 1px solid var(--color-border);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 700;
  color: var(--color-ink);
}

.stat-label {
  font-size: 12px;
  color: var(--color-muted);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

/* 动画 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .home-container {
    padding: 32px 16px 48px;
  }

  .title-line {
    font-size: 32px;
  }

  .hero-desc {
    font-size: 14px;
  }

  .form-section {
    padding: 20px;
  }

  .footer-stats {
    gap: 24px;
  }
}
</style>
