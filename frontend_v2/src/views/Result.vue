<template>
  <div class="result-container">
    <!-- 顶部导航栏 -->
    <div class="top-bar">
      <a-button class="back-btn" size="large" @click="goBack">
        <template #icon>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
        </template>
        返回
      </a-button>

      <a-space size="middle">
        <a-button v-if="tripPlan && !editMode" class="action-btn intervention-btn" @click="interventionOpen = true">⚡ 干预重规划</a-button>
        <a-button v-if="workspaceRun && !editMode" class="action-btn" @click="versionOpen = true">版本 {{ workspaceRun.versions.length }}</a-button>
        <a-button v-if="!editMode" @click="toggleEditMode" class="action-btn">
          <template #icon>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </template>
          编辑行程
        </a-button>
        <a-button v-else @click="saveChanges" type="primary" class="action-btn-primary">
          <template #icon>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/>
              <polyline points="17 21 17 13 7 13 7 21"/>
              <polyline points="7 3 7 8 15 8"/>
            </svg>
          </template>
          保存修改
        </a-button>
        <a-button v-if="editMode" @click="cancelEdit" class="action-btn">
          取消
        </a-button>

        <a-dropdown v-if="!editMode">
          <template #overlay>
            <a-menu class="export-menu">
              <a-menu-item key="image" @click="exportAsImage">
                <span class="menu-icon">📷</span> 导出为图片
              </a-menu-item>
              <a-menu-item key="pdf" @click="exportAsPDF">
                <span class="menu-icon">📄</span> 导出为PDF
              </a-menu-item>
            </a-menu>
          </template>
          <a-button class="action-btn">
            <template #icon>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
            </template>
            导出 <DownOutlined />
          </a-button>
        </a-dropdown>
      </a-space>
    </div>

    <div v-if="tripPlan" class="content-wrapper">
      <!-- 侧边导航 -->
      <div class="side-nav">
        <a-affix :offset-top="88">
          <a-menu mode="inline" :selected-keys="[activeSection]" @click="scrollToSection" class="nav-menu">
            <a-menu-item key="overview">
              <span class="nav-icon">📋</span> 行程概览
            </a-menu-item>
            <a-menu-item key="budget" v-if="tripPlan.budget">
              <span class="nav-icon">💰</span> 预算明细
            </a-menu-item>
            <a-menu-item key="map">
              <span class="nav-icon">📍</span> 景点地图
            </a-menu-item>
            <a-sub-menu key="days" title="📅 每日行程">
              <a-menu-item v-for="(day, index) in tripPlan.days" :key="`day-${index}`">
                第{{ day.day_index + 1 }}天
              </a-menu-item>
            </a-sub-menu>
            <a-menu-item key="weather" v-if="tripPlan.weather_info && tripPlan.weather_info.length > 0">
              <span class="nav-icon">🌤️</span> 天气信息
            </a-menu-item>
            <a-menu-item key="evidence" v-if="tripPlan.validation_report || tripPlan.citations?.length">
              <span class="nav-icon">✓</span> 证据与校验
            </a-menu-item>
          </a-menu>
        </a-affix>
      </div>

      <!-- 主内容区 -->
      <div class="main-content">
        <!-- 顶部信息区 -->
        <div class="top-info-section">
          <div class="left-info">
            <!-- 行程概览 -->
            <a-card id="overview" :bordered="false" class="info-card overview-card">
              <template #title>
                <div class="card-title-wrap">
                  <span class="card-title-icon">🗺️</span>
                  <span>{{ tripPlan.city }} 旅行计划</span>
                </div>
              </template>
              <div class="overview-body">
                <div class="info-row">
                  <span class="info-tag">📅 日期</span>
                  <span class="info-text">{{ tripPlan.start_date }} 至 {{ tripPlan.end_date }}</span>
                </div>
                <div class="info-row">
                  <span class="info-tag">💡 建议</span>
                  <span class="info-text">{{ tripPlan.overall_suggestions }}</span>
                </div>
              </div>
            </a-card>

            <!-- 预算明细 -->
            <a-card id="budget" v-if="tripPlan.budget" :bordered="false" class="info-card budget-card">
              <template #title>
                <div class="card-title-wrap">
                  <span class="card-title-icon">💰</span>
                  <span>预算明细</span>
                </div>
              </template>
              <div class="budget-body">
                <div class="budget-grid">
                  <div class="budget-cell">
                    <div class="budget-cell-label">景点门票</div>
                    <div class="budget-cell-value">¥{{ tripPlan.budget.total_attractions }}</div>
                  </div>
                  <div class="budget-cell">
                    <div class="budget-cell-label">酒店住宿</div>
                    <div class="budget-cell-value">¥{{ tripPlan.budget.total_hotels }}</div>
                  </div>
                  <div class="budget-cell">
                    <div class="budget-cell-label">餐饮费用</div>
                    <div class="budget-cell-value">¥{{ tripPlan.budget.total_meals }}</div>
                  </div>
                  <div class="budget-cell">
                    <div class="budget-cell-label">交通费用</div>
                    <div class="budget-cell-value">¥{{ tripPlan.budget.total_transportation }}</div>
                  </div>
                </div>
                <div class="budget-total">
                  <span>预估总费用</span>
                  <span class="budget-total-num">¥{{ tripPlan.budget.total }}</span>
                </div>
              </div>
            </a-card>
          </div>

          <div class="right-map">
            <a-card id="map" :bordered="false" class="info-card map-card">
              <template #title>
                <div class="card-title-wrap">
                  <span class="card-title-icon">📍</span>
                  <span>景点地图</span>
                </div>
              </template>
              <div id="amap-container" style="width: 100%; height: 100%"></div>
            </a-card>
          </div>
        </div>

        <a-card id="evidence" v-if="tripPlan.validation_report || tripPlan.citations?.length" :bordered="false" class="info-card evidence-card">
          <template #title>
            <div class="card-title-wrap">
              <span class="card-title-icon">✓</span>
              <span>证据与约束校验</span>
            </div>
          </template>
          <a-alert
            v-if="tripPlan.validation_report"
            :type="tripPlan.validation_report.passed ? 'success' : 'warning'"
            :message="tripPlan.validation_report.passed ? '硬性约束校验通过' : '仍有约束需要人工确认'"
            :description="`校验得分 ${Math.round(tripPlan.validation_report.score * 100)}%${tripPlan.validation_report.repair_attempted ? '，已执行一次自动重规划' : ''}`"
            show-icon
          />
          <div v-if="tripPlan.evidence_report" class="evidence-router">
            <div class="router-head">
              <div>
                <span class="router-kicker">EVIDENCE ROUTER</span>
                <strong>{{ evidenceStrategyLabel }}</strong>
              </div>
              <a-tag :color="tripPlan.evidence_report.sufficient ? 'green' : 'orange'">
                {{ tripPlan.evidence_report.sufficient ? '上下文充分' : '需要工具补证' }}
              </a-tag>
            </div>
            <p>{{ tripPlan.evidence_report.rationale }}</p>
            <div class="router-metrics">
              <span><b>{{ Math.round(tripPlan.evidence_report.coverage * 100) }}%</b>证据覆盖</span>
              <span><b>{{ tripPlan.evidence_report.retrieval_rounds }}</b>检索轮次</span>
              <span><b>{{ tripPlan.evidence_report.selected_chunks }}</b>选中片段</span>
              <span><b>{{ tripPlan.evidence_report.context_chars }}</b>上下文字符</span>
            </div>
            <div v-if="tripPlan.evidence_report.queries.length" class="query-chips">
              <span v-for="query in tripPlan.evidence_report.queries" :key="query">{{ query }}</span>
            </div>
          </div>
          <div v-if="tripPlan.optimization_report" class="solver-summary">
            <a-statistic title="CP-SAT 状态" :value="tripPlan.optimization_report.status" />
            <a-statistic title="求解耗时" :value="tripPlan.optimization_report.solver_time_ms" suffix="ms" />
            <a-statistic title="入选景点" :value="tripPlan.optimization_report.selected_attractions" />
            <a-statistic title="预计交通" :value="tripPlan.optimization_report.estimated_travel_minutes" suffix="分钟" />
          </div>
          <div v-if="tripPlan.validation_report?.issues.length" class="issue-list">
            <a-tag v-for="issue in tripPlan.validation_report.issues" :key="`${issue.code}-${issue.path}`" :color="issue.severity === 'error' ? 'red' : 'orange'">
              {{ issue.code }} · {{ issue.message }}
            </a-tag>
          </div>
          <a-list v-if="tripPlan.citations?.length" size="small" :data-source="tripPlan.citations" class="citation-list">
            <template #header><strong>本次规划引用资料</strong></template>
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="`${item.source_name} · ${item.chunk_id}`" :description="item.excerpt" />
                <span class="citation-score">{{ Math.round(item.score * 100) }}%</span>
              </a-list-item>
            </template>
          </a-list>
          <div v-if="tripPlan.planning_trace_id" class="trace-id">Trace ID: {{ tripPlan.planning_trace_id }}</div>
          <div v-if="tripPlan.planning_trace_id" class="flywheel-actions">
            <a-rate v-model:value="feedbackRating" />
            <a-input v-model:value="feedbackComment" placeholder="可选：说明满意或需要调整的原因" :maxlength="200" />
            <a-button type="primary" :loading="feedbackSubmitting" @click="sendFeedback(true)">接受方案</a-button>
            <a-button danger :loading="feedbackSubmitting" @click="sendFeedback(false)">需要调整</a-button>
            <a-button :loading="traceLoading" @click="openTrace">查看链路穿刺</a-button>
          </div>
        </a-card>

        <!-- 每日行程 -->
        <a-card title="📅 每日行程" :bordered="false" class="info-card days-card">
          <a-collapse v-model:activeKey="activeDays" accordion class="day-collapse">
            <a-collapse-panel v-for="(day, index) in tripPlan.days" :key="index" :id="`day-${index}`">
              <template #header>
                <div class="day-header">
                  <div class="day-header-left">
                    <span class="day-badge">Day {{ day.day_index + 1 }}</span>
                    <span class="day-date">{{ day.date }}</span>
                  </div>
                  <span class="day-desc">{{ day.description }}</span>
                </div>
              </template>

              <div class="day-meta">
                <div class="day-meta-item">
                  <span class="meta-label">交通</span>
                  <span class="meta-value">{{ day.transportation }}</span>
                </div>
                <div class="day-meta-item">
                  <span class="meta-label">住宿</span>
                  <span class="meta-value">{{ day.accommodation }}</span>
                </div>
              </div>

              <a-divider orientation="left" class="section-divider">景点安排</a-divider>
              <a-list :data-source="day.attractions" :grid="{ gutter: 16, column: 2 }">
                <template #renderItem="{ item, index }">
                  <a-list-item>
                    <a-card :title="item.name" size="small" class="attraction-card">
                      <template #extra>
                        <a-space v-if="editMode">
                          <a-button size="small" @click="moveAttraction(day.day_index, index, 'up')" :disabled="index === 0">
                            ↑
                          </a-button>
                          <a-button size="small" @click="moveAttraction(day.day_index, index, 'down')" :disabled="index === day.attractions.length - 1">
                            ↓
                          </a-button>
                          <a-button size="small" danger @click="deleteAttraction(day.day_index, index)">
                            🗑️
                          </a-button>
                        </a-space>
                        <a-button v-else size="small" danger ghost :loading="replanningTarget === item.name" @click="simulateClosure(day.date, item.name)">
                          模拟闭馆
                        </a-button>
                      </template>

                      <div class="attraction-image-wrap">
                        <img
                          :src="getAttractionImage(item.name, index)"
                          :alt="item.name"
                          class="attraction-image"
                          @error="handleImageError"
                        />
                        <div class="attraction-rank">{{ index + 1 }}</div>
                        <div v-if="item.ticket_price" class="attraction-price">
                          ¥{{ item.ticket_price }}
                        </div>
                      </div>

                      <div v-if="editMode" class="edit-fields">
                        <div class="edit-field">
                          <label>地址</label>
                          <a-input v-model:value="item.address" size="small" />
                        </div>
                        <div class="edit-field">
                          <label>游览时长(分钟)</label>
                          <a-input-number v-model:value="item.visit_duration" :min="10" :max="480" size="small" style="width: 100%" />
                        </div>
                        <div class="edit-field">
                          <label>描述</label>
                          <a-textarea v-model:value="item.description" :rows="2" size="small" />
                        </div>
                      </div>

                      <div v-else class="attraction-info">
                        <p><span class="attr-label">地址</span>{{ item.address }}</p>
                        <p><span class="attr-label">游览时长</span>{{ item.visit_duration }} 分钟</p>
                        <p v-if="item.scheduled_start"><span class="attr-label">求解时间</span>{{ item.scheduled_start }}—{{ item.scheduled_end }}</p>
                        <p><span class="attr-label">描述</span>{{ item.description }}</p>
                        <p v-if="item.rating"><span class="attr-label">评分</span><span class="attr-rating">{{ item.rating }} ⭐</span></p>
                      </div>
                    </a-card>
                  </a-list-item>
                </template>
              </a-list>

              <a-divider v-if="day.hotel" orientation="left" class="section-divider">住宿推荐</a-divider>
              <a-card v-if="day.hotel" size="small" class="hotel-card">
                <template #title>
                  <span class="hotel-name">{{ day.hotel.name }}</span>
                </template>
                <a-descriptions :column="2" size="small" class="hotel-desc">
                  <a-descriptions-item label="地址">{{ day.hotel.address }}</a-descriptions-item>
                  <a-descriptions-item label="类型">{{ day.hotel.type }}</a-descriptions-item>
                  <a-descriptions-item label="价格">{{ day.hotel.price_range }}</a-descriptions-item>
                  <a-descriptions-item label="评分">{{ day.hotel.rating }} ⭐</a-descriptions-item>
                  <a-descriptions-item label="距离" :span="2">{{ day.hotel.distance }}</a-descriptions-item>
                </a-descriptions>
              </a-card>

              <a-divider orientation="left" class="section-divider">餐饮安排</a-divider>
              <a-descriptions :column="1" bordered size="small" class="meal-desc">
                <a-descriptions-item v-for="meal in day.meals" :key="meal.type" :label="getMealLabel(meal.type)">
                  {{ meal.name }}
                  <span v-if="meal.description"> — {{ meal.description }}</span>
                </a-descriptions-item>
              </a-descriptions>
            </a-collapse-panel>
          </a-collapse>
        </a-card>

        <!-- 天气信息 -->
        <a-card id="weather" v-if="tripPlan.weather_info && tripPlan.weather_info.length > 0" :bordered="false" class="info-card weather-section">
          <template #title>
            <div class="card-title-wrap">
              <span class="card-title-icon">🌤️</span>
              <span>天气信息</span>
            </div>
          </template>
          <a-list :data-source="tripPlan.weather_info" :grid="{ gutter: 16, column: 3 }">
            <template #renderItem="{ item }">
              <a-list-item>
                <div class="weather-card">
                  <div class="weather-date">{{ item.date }}</div>
                  <div class="weather-row">
                    <span class="weather-icon">☀️</span>
                    <div>
                      <div class="weather-label">白天</div>
                      <div class="weather-value">{{ item.day_weather }} {{ item.day_temp }}°C</div>
                    </div>
                  </div>
                  <div class="weather-row">
                    <span class="weather-icon">🌙</span>
                    <div>
                      <div class="weather-label">夜间</div>
                      <div class="weather-value">{{ item.night_weather }} {{ item.night_temp }}°C</div>
                    </div>
                  </div>
                  <div class="weather-wind">
                    💨 {{ item.wind_direction }} {{ item.wind_power }}
                  </div>
                </div>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </div>
    </div>

    <a-empty v-else description="没有找到旅行计划数据" class="empty-state">
      <template #image>
        <div class="empty-icon">🗺️</div>
      </template>
      <template #description>
        <span class="empty-text">暂无旅行计划数据，请先创建行程</span>
      </template>
      <a-button type="primary" @click="goBack" class="empty-btn">返回首页创建行程</a-button>
    </a-empty>

    <a-modal v-model:open="traceOpen" title="端到端决策链穿刺" :footer="null" width="760px">
      <a-empty v-if="!traceData?.events?.length" description="暂无链路事件" />
      <a-timeline v-else>
        <a-timeline-item v-for="(event, index) in traceData.events" :key="index">
          <strong>{{ event.stage }} · {{ event.event_type }}</strong>
          <div class="trace-time">{{ event.created_at }}</div>
          <pre class="trace-payload">{{ JSON.stringify(event.payload, null, 2) }}</pre>
        </a-timeline-item>
      </a-timeline>
    </a-modal>

    <a-modal v-model:open="interventionOpen" title="运行中干预与局部重规划" :confirm-loading="interventionLoading" ok-text="执行重规划" cancel-text="取消" @ok="submitIntervention">
      <div class="intervention-intro">注入环境变化或用户新约束，Agent 将尽量保留未受影响的行程，仅重新求解相关日期。</div>
      <a-form layout="vertical" class="intervention-form">
        <a-form-item label="事件类型">
          <a-select v-model:value="intervention.type">
            <a-select-option value="attraction_closed">景点临时关闭</a-select-option>
            <a-select-option value="weather">天气突变</a-select-option>
            <a-select-option value="delay">交通延误</a-select-option>
            <a-select-option value="budget_changed">预算变化</a-select-option>
            <a-select-option value="user_change">用户需求变化</a-select-option>
          </a-select>
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12"><a-form-item label="影响日期"><a-select v-model:value="intervention.date" allow-clear><a-select-option v-for="day in tripPlan?.days || []" :key="day.date" :value="day.date">{{ day.date }}</a-select-option></a-select></a-form-item></a-col>
          <a-col v-if="intervention.type === 'delay'" :span="12"><a-form-item label="延误时间（分钟）"><a-input-number v-model:value="intervention.delay_minutes" :min="0" style="width:100%" /></a-form-item></a-col>
          <a-col v-else-if="intervention.type === 'budget_changed'" :span="12"><a-form-item label="新预算"><a-input-number v-model:value="intervention.new_budget" :min="0" style="width:100%" /></a-form-item></a-col>
          <a-col v-else :span="12"><a-form-item label="影响对象"><a-input v-model:value="intervention.target" placeholder="景点、区域或交通方式" /></a-form-item></a-col>
        </a-row>
        <a-form-item label="事件描述"><a-textarea v-model:value="intervention.description" :rows="3" placeholder="例如：下午持续降雨，希望改为室内活动" /></a-form-item>
      </a-form>
    </a-modal>

    <a-drawer v-model:open="versionOpen" title="方案版本历史" width="420">
      <div v-if="workspaceRun" class="version-list">
        <button v-for="version in [...workspaceRun.versions].reverse()" :key="version.id" class="version-item" @click="restoreVersion(version)">
          <span class="version-node" :class="{ current: version.traceId === tripPlan?.planning_trace_id }"></span>
          <span class="version-copy"><strong>v{{ version.revision }} · {{ version.reason }}</strong><small>{{ formatVersionTime(version.createdAt) }}</small><code>{{ version.traceId || 'manual-edit' }}</code></span>
          <span class="version-action">查看</span>
        </button>
      </div>
    </a-drawer>

    <a-back-top :visibility-height="300">
      <div class="back-top-btn">↑</div>
    </a-back-top>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { DownOutlined } from '@ant-design/icons-vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import { getPlanningTrace, replanTrip, submitTripFeedback } from '@/services/api'
import { getActiveRunId, listWorkspaceRuns, openWorkspaceRun, updateWorkspaceFeedback, updateWorkspaceRun, type PlanVersion, type WorkspaceRun } from '@/services/workspace'
import type { Disruption, TripFormData, TripPlan } from '@/types'

const router = useRouter()
const tripPlan = ref<TripPlan | null>(null)
const replanningTarget = ref('')
const feedbackRating = ref(5)
const feedbackComment = ref('')
const feedbackSubmitting = ref(false)
const traceOpen = ref(false)
const traceLoading = ref(false)
const traceData = ref<any>(null)
const workspaceRun = ref<WorkspaceRun | null>(null)
const interventionOpen = ref(false)
const interventionLoading = ref(false)
const versionOpen = ref(false)
const intervention = ref<Disruption>({ type: 'weather', delay_minutes: 0, description: '' })
const evidenceStrategyLabel = computed(() => {
  const labels: Record<string, string> = {
    tool_first: 'Tool-first 实时证据',
    long_context: 'Long Context 完整资料',
    hybrid_multi_query: 'Hybrid Multi-query 多路召回'
  }
  return labels[tripPlan.value?.evidence_report?.strategy || ''] || tripPlan.value?.evidence_report?.strategy || '未路由'
})

const refreshWorkspaceRun = () => {
  workspaceRun.value = listWorkspaceRuns().find(run => run.id === getActiveRunId()) || null
}

const sendFeedback = async (accepted: boolean) => {
  if (!tripPlan.value?.planning_trace_id) return
  feedbackSubmitting.value = true
  try {
    await submitTripFeedback(
      tripPlan.value.planning_trace_id,
      accepted,
      feedbackRating.value,
      feedbackComment.value
    )
    updateWorkspaceFeedback(accepted, feedbackRating.value, feedbackComment.value)
    refreshWorkspaceRun()
    message.success(accepted ? '已记录接受反馈' : '已进入飞轮难例候选')
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '反馈提交失败')
  } finally {
    feedbackSubmitting.value = false
  }
}

const openTrace = async () => {
  if (!tripPlan.value?.planning_trace_id) return
  traceLoading.value = true
  try {
    traceData.value = await getPlanningTrace(tripPlan.value.planning_trace_id)
    traceOpen.value = true
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '链路读取失败')
  } finally {
    traceLoading.value = false
  }
}

const simulateClosure = async (date: string, attractionName: string) => {
  if (!tripPlan.value) return
  const requestJson = sessionStorage.getItem('tripRequest')
  if (!requestJson) {
    message.error('缺少原始规划请求，请返回首页重新生成')
    return
  }
  replanningTarget.value = attractionName
  try {
    const request = JSON.parse(requestJson) as TripFormData
    const response = await replanTrip(request, tripPlan.value, {
      type: 'attraction_closed',
      date,
      target: attractionName,
      description: `${attractionName} 临时闭馆`
    })
    if (response.success && response.data) {
      tripPlan.value = response.data
      sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
      updateWorkspaceRun(response.data, `${attractionName}闭馆重规划`)
      refreshWorkspaceRun()
      message.success(`已完成局部重规划，版本更新至 v${response.data.revision}`)
    }
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '局部重规划失败')
  } finally {
    replanningTarget.value = ''
  }
}

const submitIntervention = async () => {
  if (!tripPlan.value) return
  const requestJson = sessionStorage.getItem('tripRequest')
  if (!requestJson) return message.error('缺少原始规划请求')
  interventionLoading.value = true
  try {
    const response = await replanTrip(JSON.parse(requestJson), tripPlan.value, intervention.value)
    if (response.success && response.data) {
      tripPlan.value = response.data
      sessionStorage.setItem('tripPlan', JSON.stringify(response.data))
      const labels: Record<string, string> = { attraction_closed: '闭馆事件', weather: '天气变化', delay: '交通延误', budget_changed: '预算调整', user_change: '需求变更' }
      updateWorkspaceRun(response.data, `${labels[intervention.value.type]}重规划`)
      refreshWorkspaceRun()
      interventionOpen.value = false
      message.success(`局部重规划完成，已生成 v${response.data.revision}`)
      if (map) map.destroy()
      await nextTick()
      initMap()
    }
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '重规划失败')
  } finally {
    interventionLoading.value = false
  }
}

const restoreVersion = async (version: PlanVersion) => {
  if (!workspaceRun.value) return
  openWorkspaceRun(workspaceRun.value, version)
  tripPlan.value = JSON.parse(JSON.stringify(version.plan))
  versionOpen.value = false
  message.info(`已切换至 v${version.revision} 只读快照`)
  if (map) map.destroy()
  await nextTick()
  initMap()
}

const formatVersionTime = (value: string) => new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
const editMode = ref(false)
const originalPlan = ref<TripPlan | null>(null)
const attractionPhotos = ref<Record<string, string>>({})
const activeSection = ref('overview')
const activeDays = ref<number[]>([0])
let map: any = null

onMounted(async () => {
  refreshWorkspaceRun()
  const data = sessionStorage.getItem('tripPlan')
  if (data) {
    tripPlan.value = JSON.parse(data)
    await loadAttractionPhotos()
    await nextTick()
    initMap()
  }
})

const goBack = () => router.push('/')

const scrollToSection = ({ key }: { key: string }) => {
  activeSection.value = key
  const el = document.getElementById(key)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const toggleEditMode = () => {
  editMode.value = true
  originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
  message.info('进入编辑模式')
}

const saveChanges = () => {
  editMode.value = false
  if (tripPlan.value) {
    sessionStorage.setItem('tripPlan', JSON.stringify(tripPlan.value))
    updateWorkspaceRun(tripPlan.value, '人工编辑')
    refreshWorkspaceRun()
  }
  message.success('修改已保存')
  if (map) map.destroy()
  nextTick(() => initMap())
}

const cancelEdit = () => {
  if (originalPlan.value) tripPlan.value = JSON.parse(JSON.stringify(originalPlan.value))
  editMode.value = false
  message.info('已取消编辑')
}

const deleteAttraction = (dayIndex: number, attrIndex: number) => {
  if (!tripPlan.value) return
  const day = tripPlan.value.days[dayIndex]
  if (day.attractions.length <= 1) {
    message.warning('每天至少需要保留一个景点')
    return
  }
  day.attractions.splice(attrIndex, 1)
  message.success('景点已删除')
}

const moveAttraction = (dayIndex: number, attrIndex: number, direction: 'up' | 'down') => {
  if (!tripPlan.value) return
  const attractions = tripPlan.value.days[dayIndex].attractions
  if (direction === 'up' && attrIndex > 0) {
    [attractions[attrIndex], attractions[attrIndex - 1]] = [attractions[attrIndex - 1], attractions[attrIndex]]
  } else if (direction === 'down' && attrIndex < attractions.length - 1) {
    [attractions[attrIndex], attractions[attrIndex + 1]] = [attractions[attrIndex + 1], attractions[attrIndex]]
  }
}

const getMealLabel = (type: string): string => {
  const labels: Record<string, string> = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '小吃' }
  return labels[type] || type
}

const loadAttractionPhotos = async () => {
  if (!tripPlan.value) return
  const promises: Promise<void>[] = []
  tripPlan.value.days.forEach(day => {
    day.attractions.forEach(attraction => {
      const promise = fetch(`http://localhost:8000/api/poi/photo?name=${encodeURIComponent(attraction.name)}`)
        .then(res => res.json())
        .then(data => {
          if (data.success && data.data.photo_url) {
            attractionPhotos.value[attraction.name] = data.data.photo_url
          }
        })
        .catch(err => console.error(`获取${attraction.name}图片失败:`, err))
      promises.push(promise)
    })
  })
  await Promise.all(promises)
}

const getAttractionImage = (name: string, index: number): string => {
  if (attractionPhotos.value[name]) return attractionPhotos.value[name]
  const colors = [
    { start: '#1a1a2e', end: '#16213e' },
    { start: '#0f3460', end: '#1a1a2e' },
    { start: '#e94560', end: '#0f3460' },
    { start: '#16213e', end: '#0f3460' },
    { start: '#1a1a2e', end: '#e94560' }
  ]
  const { start, end } = colors[index % colors.length]
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
    <defs>
      <linearGradient id="g${index}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:${start};stop-opacity:1" />
        <stop offset="100%" style="stop-color:${end};stop-opacity:1" />
      </linearGradient>
    </defs>
    <rect width="400" height="300" fill="url(#g${index})"/>
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="22" font-weight="bold" fill="white">${name}</text>
  </svg>`
  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`
}

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect width="400" height="300" fill="%23f0f0f0"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="16" fill="%23999"%3E图片加载失败%3C/text%3E%3C/svg%3E'
}

const exportAsImage = async () => {
  try {
    message.loading({ content: '正在生成图片...', key: 'export', duration: 0 })
    const element = document.querySelector('.main-content') as HTMLElement
    if (!element) throw new Error('未找到内容元素')

    const exportContainer = document.createElement('div')
    exportContainer.style.width = element.offsetWidth + 'px'
    exportContainer.style.backgroundColor = '#faf9f6'
    exportContainer.style.padding = '20px'
    exportContainer.innerHTML = element.innerHTML

    const mapContainer = document.getElementById('amap-container')
    if (mapContainer && map) {
      const mapCanvas = mapContainer.querySelector('canvas')
      if (mapCanvas) {
        const mapSnapshot = mapCanvas.toDataURL('image/png')
        const exportMapContainer = exportContainer.querySelector('#amap-container')
        if (exportMapContainer) {
          exportMapContainer.innerHTML = `<img src="${mapSnapshot}" style="width:100%;height:100%;object-fit:cover;" />`
        }
      }
    }

    const cards = exportContainer.querySelectorAll('.ant-card')
    cards.forEach((card) => {
      const cardEl = card as HTMLElement
      try {
        cardEl.className = ''
        cardEl.style.setProperty('background-color', '#ffffff')
        cardEl.style.setProperty('border-radius', '12px')
        cardEl.style.setProperty('box-shadow', '0 4px 12px rgba(0,0,0,0.08)')
        cardEl.style.setProperty('margin-bottom', '20px')
        cardEl.style.setProperty('overflow', 'hidden')
      } catch (err) { console.error('设置卡片样式失败:', err) }
    })

    const cardHeads = exportContainer.querySelectorAll('.ant-card-head')
    cardHeads.forEach((head) => {
      const headEl = head as HTMLElement
      try {
        headEl.style.setProperty('background-color', '#1a1a2e')
        headEl.style.setProperty('color', '#ffffff')
        headEl.style.setProperty('padding', '16px 24px')
        headEl.style.setProperty('font-size', '16px')
        headEl.style.setProperty('font-weight', '600')
      } catch (err) { console.error('设置卡片头部样式失败:', err) }
    })

    const cardBodies = exportContainer.querySelectorAll('.ant-card-body')
    cardBodies.forEach((body) => {
      const bodyEl = body as HTMLElement
      bodyEl.style.setProperty('background-color', '#ffffff')
      bodyEl.style.setProperty('padding', '24px')
    })

    const hotelCards = exportContainer.querySelectorAll('.hotel-card')
    hotelCards.forEach((card) => {
      const head = card.querySelector('.ant-card-head') as HTMLElement
      if (head) head.style.setProperty('background-color', '#0f3460')
      ;(card as HTMLElement).style.setProperty('background-color', '#f0f4f8')
    })

    const weatherCards = exportContainer.querySelectorAll('.weather-card')
    weatherCards.forEach((card) => {
      (card as HTMLElement).style.setProperty('background-color', '#f0f7fa')
    })

    const budgetTotal = exportContainer.querySelector('.budget-total')
    if (budgetTotal) {
      const el = budgetTotal as HTMLElement
      el.style.setProperty('background-color', '#1a1a2e')
      el.style.setProperty('color', '#ffffff')
      el.style.setProperty('padding', '16px 20px')
      el.style.setProperty('border-radius', '10px')
    }

    const budgetCells = exportContainer.querySelectorAll('.budget-cell')
    budgetCells.forEach((item) => {
      const el = item as HTMLElement
      el.style.setProperty('background-color', '#faf9f6')
      el.style.setProperty('padding', '12px')
      el.style.setProperty('border-radius', '8px')
    })

    exportContainer.style.position = 'absolute'
    exportContainer.style.left = '-9999px'
    document.body.appendChild(exportContainer)

    const canvas = await html2canvas(exportContainer, {
      backgroundColor: '#faf9f6',
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true
    })

    document.body.removeChild(exportContainer)

    const link = document.createElement('a')
    link.download = `旅行计划_${tripPlan.value?.city}_${new Date().getTime()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()

    message.success({ content: '图片导出成功!', key: 'export' })
  } catch (error: any) {
    console.error('导出图片失败:', error)
    message.error({ content: `导出图片失败: ${error.message}`, key: 'export' })
  }
}

const exportAsPDF = async () => {
  try {
    message.loading({ content: '正在生成PDF...', key: 'export', duration: 0 })
    const element = document.querySelector('.main-content') as HTMLElement
    if (!element) throw new Error('未找到内容元素')

    const exportContainer = document.createElement('div')
    exportContainer.style.width = element.offsetWidth + 'px'
    exportContainer.style.backgroundColor = '#faf9f6'
    exportContainer.style.padding = '20px'
    exportContainer.innerHTML = element.innerHTML

    const mapContainer = document.getElementById('amap-container')
    if (mapContainer && map) {
      const mapCanvas = mapContainer.querySelector('canvas')
      if (mapCanvas) {
        const mapSnapshot = mapCanvas.toDataURL('image/png')
        const exportMapContainer = exportContainer.querySelector('#amap-container')
        if (exportMapContainer) {
          exportMapContainer.innerHTML = `<img src="${mapSnapshot}" style="width:100%;height:100%;object-fit:cover;" />`
        }
      }
    }

    const cards = exportContainer.querySelectorAll('.ant-card')
    cards.forEach((card) => {
      const cardEl = card as HTMLElement
      try {
        cardEl.className = ''
        cardEl.style.setProperty('background-color', '#ffffff')
        cardEl.style.setProperty('border-radius', '12px')
        cardEl.style.setProperty('box-shadow', '0 4px 12px rgba(0,0,0,0.08)')
        cardEl.style.setProperty('margin-bottom', '20px')
        cardEl.style.setProperty('overflow', 'hidden')
      } catch (err) { console.error('设置卡片样式失败:', err) }
    })

    const cardHeads = exportContainer.querySelectorAll('.ant-card-head')
    cardHeads.forEach((head) => {
      const headEl = head as HTMLElement
      try {
        headEl.style.setProperty('background-color', '#1a1a2e')
        headEl.style.setProperty('color', '#ffffff')
        headEl.style.setProperty('padding', '16px 24px')
        headEl.style.setProperty('font-size', '16px')
        headEl.style.setProperty('font-weight', '600')
      } catch (err) { console.error('设置卡片头部样式失败:', err) }
    })

    const cardBodies = exportContainer.querySelectorAll('.ant-card-body')
    cardBodies.forEach((body) => {
      const bodyEl = body as HTMLElement
      bodyEl.style.setProperty('background-color', '#ffffff')
      bodyEl.style.setProperty('padding', '24px')
    })

    const hotelCards = exportContainer.querySelectorAll('.hotel-card')
    hotelCards.forEach((card) => {
      const head = card.querySelector('.ant-card-head') as HTMLElement
      if (head) head.style.setProperty('background-color', '#0f3460')
      ;(card as HTMLElement).style.setProperty('background-color', '#f0f4f8')
    })

    const weatherCards = exportContainer.querySelectorAll('.weather-card')
    weatherCards.forEach((card) => {
      (card as HTMLElement).style.setProperty('background-color', '#f0f7fa')
    })

    const budgetTotal = exportContainer.querySelector('.budget-total')
    if (budgetTotal) {
      const el = budgetTotal as HTMLElement
      el.style.setProperty('background-color', '#1a1a2e')
      el.style.setProperty('color', '#ffffff')
      el.style.setProperty('padding', '16px 20px')
      el.style.setProperty('border-radius', '10px')
    }

    const budgetCells = exportContainer.querySelectorAll('.budget-cell')
    budgetCells.forEach((item) => {
      const el = item as HTMLElement
      el.style.setProperty('background-color', '#faf9f6')
      el.style.setProperty('padding', '12px')
      el.style.setProperty('border-radius', '8px')
    })

    exportContainer.style.position = 'absolute'
    exportContainer.style.left = '-9999px'
    document.body.appendChild(exportContainer)

    const canvas = await html2canvas(exportContainer, {
      backgroundColor: '#faf9f6',
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true
    })

    document.body.removeChild(exportContainer)

    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
    const imgWidth = 210
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    let heightLeft = imgHeight
    let position = 0

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= 297
    while (heightLeft > 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= 297
    }

    pdf.save(`旅行计划_${tripPlan.value?.city}_${new Date().getTime()}.pdf`)
    message.success({ content: 'PDF导出成功!', key: 'export' })
  } catch (error: any) {
    console.error('导出PDF失败:', error)
    message.error({ content: `导出PDF失败: ${error.message}`, key: 'export' })
  }
}

const initMap = async () => {
  try {
    const AMap = await AMapLoader.load({
      key: import.meta.env.VITE_AMAP_WEB_JS_KEY,
      version: '2.0',
      plugins: ['AMap.Marker', 'AMap.Polyline', 'AMap.InfoWindow']
    })

    map = new AMap.Map('amap-container', {
      zoom: 12,
      center: [116.397128, 39.916527],
      viewMode: '3D'
    })

    addAttractionMarkers(AMap)
    message.success('地图加载成功')
  } catch (error) {
    console.error('地图加载失败:', error)
    message.error('地图加载失败')
  }
}

const addAttractionMarkers = (AMap: any) => {
  if (!tripPlan.value) return
  const markers: any[] = []
  const allAttractions: any[] = []

  tripPlan.value.days.forEach((day, dayIndex) => {
    day.attractions.forEach((attraction, attrIndex) => {
      if (attraction.location && attraction.location.longitude && attraction.location.latitude) {
        allAttractions.push({ ...attraction, dayIndex, attrIndex })
      }
    })
  })

  allAttractions.forEach((attraction, index) => {
    const marker = new AMap.Marker({
      position: [attraction.location.longitude, attraction.location.latitude],
      title: attraction.name,
      label: {
        content: `<div style="background: #e94560; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">${index + 1}</div>`,
        offset: new AMap.Pixel(0, -30)
      }
    })

    const infoWindow = new AMap.InfoWindow({
      content: `
        <div style="padding: 12px; font-family: sans-serif;">
          <h4 style="margin: 0 0 8px 0; font-size: 15px; color: #1a1a2e;">${attraction.name}</h4>
          <p style="margin: 4px 0; font-size: 12px; color: #555;"><strong>地址:</strong> ${attraction.address}</p>
          <p style="margin: 4px 0; font-size: 12px; color: #555;"><strong>游览时长:</strong> ${attraction.visit_duration}分钟</p>
          <p style="margin: 4px 0; font-size: 12px; color: #555;"><strong>描述:</strong> ${attraction.description}</p>
          <p style="margin: 4px 0; font-size: 12px; color: #e94560; font-weight: 600;">第${attraction.dayIndex + 1}天 景点${attraction.attrIndex + 1}</p>
        </div>
      `,
      offset: new AMap.Pixel(0, -30)
    })

    marker.on('click', () => infoWindow.open(map, marker.getPosition()))
    markers.push(marker)
  })

  map.add(markers)
  if (allAttractions.length > 0) map.setFitView(markers)
  drawRoutes(AMap, allAttractions)
}

const drawRoutes = (AMap: any, attractions: any[]) => {
  if (attractions.length < 2) return
  const dayGroups: any = {}
  attractions.forEach(attr => {
    if (!dayGroups[attr.dayIndex]) dayGroups[attr.dayIndex] = []
    dayGroups[attr.dayIndex].push(attr)
  })

  Object.values(dayGroups).forEach((dayAttractions: any) => {
    if (dayAttractions.length < 2) return
    const path = dayAttractions.map((attr: any) => [attr.location.longitude, attr.location.latitude])
    const polyline = new AMap.Polyline({
      path,
      strokeColor: '#0f3460',
      strokeWeight: 3,
      strokeOpacity: 0.7,
      strokeStyle: 'solid',
      showDir: true
    })
    map.add(polyline)
  })
}
</script>

<style scoped>
.result-container {
  min-height: 100vh;
  background: var(--color-cream);
  padding: 32px 24px 60px;
}

/* 顶部栏 */
.top-bar {
  max-width: 1280px;
  margin: 0 auto 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: fadeInDown 0.5s ease-out;
}

.back-btn {
  border-radius: 10px;
  font-weight: 500;
  border: 1px solid var(--color-border);
  background: var(--color-paper);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.back-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.action-btn {
  border-radius: 10px;
  border: 1px solid var(--color-border);
  background: var(--color-paper);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.action-btn-primary {
  border-radius: 10px;
  background: var(--color-ink);
  border: none;
  color: white;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.action-btn-primary:hover {
  background: var(--color-slate);
}

.intervention-btn {
  border-color: rgba(233, 69, 96, .3);
  color: var(--color-warm);
  background: rgba(233, 69, 96, .05);
}

.intervention-intro {
  margin-bottom: 20px;
  padding: 13px 15px;
  border-left: 3px solid var(--color-accent);
  border-radius: 0 8px 8px 0;
  background: #f4f7fb;
  color: #5f6878;
  font-size: 13px;
  line-height: 1.7;
}

.intervention-form :deep(.ant-form-item) { margin-bottom: 15px; }

.version-list { display: flex; flex-direction: column; }
.version-item {
  display: grid;
  grid-template-columns: 14px 1fr auto;
  gap: 12px;
  align-items: flex-start;
  padding: 17px 8px;
  border: 0;
  border-bottom: 1px solid #edf0f4;
  background: #fff;
  text-align: left;
  cursor: pointer;
}
.version-item:hover { background: #f7f9fc; }
.version-node { width: 10px; height: 10px; margin-top: 4px; border: 2px solid #abb4c4; border-radius: 50%; }
.version-node.current { border-color: #35b981; background: #35b981; box-shadow: 0 0 0 4px rgba(53,185,129,.12); }
.version-copy { display: flex; min-width: 0; flex-direction: column; gap: 4px; }
.version-copy strong { color: #1e2942; font-size: 13px; }
.version-copy small { color: #8c95a6; font-size: 11px; }
.version-copy code { overflow: hidden; color: #7d8799; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.version-action { color: var(--color-accent); font-size: 12px; }

.export-menu :deep(.ant-dropdown-menu-item) {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 内容布局 */
.content-wrapper {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  gap: 24px;
}

.side-nav {
  width: 220px;
  flex-shrink: 0;
}

.nav-menu :deep(.ant-menu) {
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(26, 26, 46, 0.04), 0 8px 24px rgba(26, 26, 46, 0.04);
  background: var(--color-paper);
  border: 1px solid var(--color-border);
  padding: 8px 0;
}

.nav-menu :deep(.ant-menu-item) {
  margin: 2px 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  height: 40px;
  line-height: 40px;
}

.nav-menu :deep(.ant-menu-item-selected) {
  background: var(--color-ink) !important;
  color: white !important;
}

.nav-menu :deep(.ant-menu-item:hover:not(.ant-menu-item-selected)) {
  background: rgba(15, 52, 96, 0.06);
}

.nav-icon {
  margin-right: 6px;
}

.main-content {
  flex: 1;
  min-width: 0;
}

/* 信息卡片通用 */
.info-card {
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(26, 26, 46, 0.04), 0 8px 24px rgba(26, 26, 46, 0.04);
  background: var(--color-paper) !important;
  border: 1px solid var(--color-border) !important;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.info-card:hover {
  box-shadow: 0 1px 3px rgba(26, 26, 46, 0.06), 0 12px 32px rgba(26, 26, 46, 0.08);
}

.info-card :deep(.ant-card-head) {
  background: transparent;
  border-bottom: 1px solid var(--color-border);
  padding: 16px 20px;
  min-height: 56px;
}

.info-card :deep(.ant-card-head-title) {
  font-weight: 600;
  font-size: 15px;
  color: var(--color-ink);
}

.card-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title-icon {
  font-size: 18px;
}

/* 顶部信息区 */
.top-info-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.left-info {
  flex: 0 0 380px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.right-map {
  flex: 1;
}

.overview-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-text {
  font-size: 14px;
  color: var(--color-slate);
  line-height: 1.6;
}

/* 预算 */
.budget-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.evidence-card {
  margin-bottom: 24px;
}

.solver-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 16px 0;
  padding: 16px;
  border-radius: 12px;
  background: rgba(15, 52, 96, 0.05);
}

.evidence-router { margin: 16px 0; padding: 16px; border: 1px solid #dfe7f3; border-radius: 12px; background: linear-gradient(135deg,#f7f9fd,#fff); }
.router-head { display:flex; justify-content:space-between; align-items:center; gap:12px; }
.router-head>div { display:flex; flex-direction:column; gap:3px; }
.router-kicker { color:#70809b; font-size:9px; font-weight:800; letter-spacing:1.4px; }
.router-head strong { color:#1d2b48; font-size:15px; }
.evidence-router>p { margin:12px 0; color:#6d778a; font-size:12px; line-height:1.7; }
.router-metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }
.router-metrics span { display:flex; flex-direction:column; padding:9px 10px; border-radius:8px; background:#fff; color:#8b94a5; font-size:10px; }
.router-metrics b { color:#243354; font-size:16px; }
.query-chips { display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; }
.query-chips span { padding:4px 8px; border-radius:999px; background:#edf2fb; color:#48638f; font-size:10px; }
@media(max-width:700px){.router-metrics{grid-template-columns:repeat(2,1fr)}}

@media (max-width: 768px) {
  .solver-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.issue-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 16px 0;
}

.citation-list {
  margin-top: 16px;
}

.citation-score {
  color: #0f3460;
  font-weight: 600;
}

.trace-id {
  margin-top: 12px;
  color: #8c8c8c;
  font-family: monospace;
  font-size: 12px;
}

.flywheel-actions {
  display: grid;
  grid-template-columns: auto minmax(220px, 1fr) auto auto auto;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.trace-time {
  margin: 3px 0 8px;
  color: #8c8c8c;
  font-size: 12px;
}

.trace-payload {
  max-height: 220px;
  overflow: auto;
  padding: 10px;
  border-radius: 8px;
  background: #f7f8fa;
  font-size: 12px;
  white-space: pre-wrap;
}

@media (max-width: 900px) {
  .flywheel-actions {
    grid-template-columns: 1fr;
  }
}

.budget-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.budget-cell {
  text-align: center;
  padding: 12px;
  background: var(--color-cream);
  border-radius: 10px;
  border: 1px solid var(--color-border);
}

.budget-cell-label {
  font-size: 11px;
  color: var(--color-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.budget-cell-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-ink);
}

.budget-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: var(--color-ink);
  border-radius: 10px;
  color: white;
  font-size: 14px;
}

.budget-total-num {
  font-size: 24px;
  font-weight: 700;
}

/* 地图 */
.map-card {
  height: 100%;
  min-height: 480px;
}

.map-card :deep(.ant-card-body) {
  height: calc(100% - 56px);
  padding: 0;
  border-radius: 0 0 16px 16px;
  overflow: hidden;
}

/* 每日行程 */
.days-card :deep(.ant-card-body) {
  padding: 20px;
}

.day-collapse :deep(.ant-collapse) {
  border: none;
  background: transparent;
}

.day-collapse :deep(.ant-collapse-item) {
  margin-bottom: 12px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--color-paper);
}

.day-collapse :deep(.ant-collapse-header) {
  background: var(--color-cream);
  padding: 14px 18px !important;
  font-weight: 600;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 12px;
}

.day-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.day-badge {
  background: var(--color-ink);
  color: white;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
}

.day-date {
  font-size: 13px;
  color: var(--color-muted);
  font-weight: 400;
}

.day-desc {
  font-size: 13px;
  color: var(--color-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.day-meta {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: var(--color-cream);
  border-radius: 10px;
}

.day-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.meta-label {
  font-size: 11px;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.meta-value {
  font-size: 13px;
  color: var(--color-slate);
  font-weight: 500;
}

.section-divider :deep(.ant-divider-inner-text) {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 景点卡片 */
.attraction-card :deep(.ant-card-head) {
  background: var(--color-cream);
  min-height: 44px;
  padding: 10px 14px;
}

.attraction-card :deep(.ant-card-head-title) {
  font-size: 14px;
}

.attraction-image-wrap {
  position: relative;
  margin-bottom: 12px;
  border-radius: 10px;
  overflow: hidden;
}

.attraction-image {
  width: 100%;
  height: 180px;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.attraction-image-wrap:hover .attraction-image {
  transform: scale(1.03);
}

.attraction-rank {
  position: absolute;
  top: 10px;
  left: 10px;
  background: var(--color-warm);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

.attraction-price {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(233, 69, 96, 0.9);
  color: white;
  padding: 3px 10px;
  border-radius: 100px;
  font-weight: 600;
  font-size: 12px;
}

.attraction-info p {
  margin: 4px 0;
  font-size: 13px;
  color: var(--color-slate);
  line-height: 1.5;
}

.attr-label {
  display: inline-block;
  min-width: 64px;
  color: var(--color-muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-right: 6px;
}

.attr-rating {
  color: var(--color-warm);
  font-weight: 600;
}

.edit-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.edit-field label {
  font-size: 11px;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
  display: block;
}

/* 酒店卡片 */
.hotel-card {
  background: linear-gradient(135deg, #f0f4f8 0%, #e8eef5 100%);
  border: none !important;
}

.hotel-card :deep(.ant-card-head) {
  background: var(--color-accent);
  min-height: 40px;
  padding: 8px 14px;
}

.hotel-name {
  color: white !important;
  font-weight: 600;
  font-size: 14px;
}

.hotel-desc :deep(.ant-descriptions-item-label) {
  font-size: 11px;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.hotel-desc :deep(.ant-descriptions-item-content) {
  font-size: 13px;
  color: var(--color-slate);
}

/* 餐饮 */
.meal-desc :deep(.ant-descriptions-item-label) {
  font-size: 11px;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  width: 60px;
}

.meal-desc :deep(.ant-descriptions-item-content) {
  font-size: 13px;
  color: var(--color-slate);
}

/* 天气 */
.weather-section :deep(.ant-card-body) {
  padding: 20px;
}

.weather-card {
  background: linear-gradient(135deg, #e8f4f8 0%, #dceef5 100%);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(15, 52, 96, 0.08);
  transition: all 0.3s ease;
}

.weather-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(15, 52, 96, 0.1);
}

.weather-date {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-accent);
  margin-bottom: 12px;
  text-align: center;
}

.weather-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.weather-icon {
  font-size: 22px;
}

.weather-label {
  font-size: 11px;
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.weather-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-accent);
}

.weather-wind {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(15, 52, 96, 0.1);
  text-align: center;
  color: var(--color-accent);
  font-size: 12px;
}

/* 回到顶部 */
.back-top-btn {
  width: 44px;
  height: 44px;
  background: var(--color-ink);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(26, 26, 46, 0.3);
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-top-btn:hover {
  transform: scale(1.08);
  background: var(--color-warm);
}

/* 空状态 */
.empty-state {
  margin-top: 80px;
}

.empty-icon {
  font-size: 72px;
  margin-bottom: 16px;
}

.empty-text {
  color: var(--color-muted);
  font-size: 14px;
}

.empty-btn {
  margin-top: 16px;
  background: var(--color-ink);
  border: none;
  border-radius: 10px;
}

/* 动画 */
@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-16px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 响应式 */
@media (max-width: 1024px) {
  .top-info-section {
    flex-direction: column;
  }
  .left-info {
    flex: 1;
  }
  .side-nav {
    display: none;
  }
}

@media (max-width: 768px) {
  .result-container {
    padding: 16px 12px 40px;
  }
  .top-bar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  .day-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  .day-desc {
    max-width: 100%;
  }
}
</style>
