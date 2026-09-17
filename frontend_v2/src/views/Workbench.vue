<template>
  <div class="workbench-page">
    <section class="workbench-hero">
      <div>
        <div class="eyebrow"><span class="live-dot"></span> AGENT OPERATIONS</div>
        <h1>旅行规划 Agent 工作台</h1>
        <p>统一管理任务运行、约束求解、链路证据、方案版本与反馈数据。</p>
      </div>
      <a-button type="primary" size="large" class="new-run-btn" @click="router.push('/plan')">＋ 新建规划任务</a-button>
    </section>

    <section class="metric-grid">
      <div class="metric-card">
        <span class="metric-label">本地任务</span>
        <strong>{{ runs.length }}</strong>
        <span class="metric-note">最近保留 50 条运行</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">约束通过率</span>
        <strong>{{ validationRate }}%</strong>
        <span class="metric-note">基于当前工作区结果</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">平均校验分</span>
        <strong>{{ averageScore }}%</strong>
        <span class="metric-note">硬约束与事实一致性</span>
      </div>
      <div class="metric-card accent-card">
        <span class="metric-label">难例候选</span>
        <strong>{{ hardCaseCount }}</strong>
        <span class="metric-note">修复、重规划或拒绝样本</span>
      </div>
    </section>

    <section class="workspace-grid">
      <div class="panel run-panel">
        <div class="panel-head">
          <div><span class="panel-kicker">RUNS</span><h2>任务运行</h2></div>
          <a-input v-model:value="keyword" allow-clear placeholder="搜索城市或任务" class="run-search" />
        </div>
        <div v-if="filteredRuns.length" class="run-list">
          <button v-for="run in filteredRuns" :key="run.id" class="run-row" @click="openRun(run)">
            <span class="run-status" :class="run.status"></span>
            <span class="run-main">
              <strong>{{ run.title }}</strong>
              <small>{{ run.request.start_date }} — {{ run.request.end_date }} · {{ run.request.transportation }}</small>
            </span>
            <span class="run-signals">
              <a-tag :color="run.plan.validation_report?.passed === false ? 'orange' : 'green'">
                {{ run.plan.validation_report?.passed === false ? '待复核' : '已通过' }}
              </a-tag>
              <small>v{{ run.plan.revision || 0 }} · {{ run.versions.length }} 个版本</small>
            </span>
            <span class="run-time">{{ formatTime(run.updatedAt) }}</span>
            <span class="row-arrow">→</span>
          </button>
        </div>
        <div v-else class="empty-runs">
          <div class="empty-mark">◎</div>
          <h3>{{ keyword ? '没有匹配的任务' : '工作区还没有运行记录' }}</h3>
          <p>创建任务后，规划结果、Trace 和方案版本会汇总到这里。</p>
          <a-button v-if="!keyword" @click="router.push('/plan')">创建第一个任务</a-button>
        </div>
      </div>

      <aside class="side-stack">
        <div class="panel pipeline-panel">
          <div class="panel-head compact"><div><span class="panel-kicker">PIPELINE</span><h2>运行链路</h2></div></div>
          <div class="pipeline">
            <div v-for="(stage, index) in stages" :key="stage.name" class="pipeline-step">
              <span class="stage-index">{{ String(index + 1).padStart(2, '0') }}</span>
              <div><strong>{{ stage.name }}</strong><small>{{ stage.desc }}</small></div>
              <span class="stage-state">READY</span>
            </div>
          </div>
        </div>
        <div class="panel flywheel-panel">
          <div class="flywheel-title"><span>↻</span><div><small>DATA FLYWHEEL</small><h2>质量反馈闭环</h2></div></div>
          <p>将低分、自动修复、动态重规划和用户拒绝样本沉淀为难例，用于后续评测与策略迭代。</p>
          <div class="flywheel-stats">
            <span><strong>{{ serverStats.episodes || runs.length }}</strong>规划样本</span>
            <span><strong>{{ serverStats.feedback || feedbackCount }}</strong>用户反馈</span>
            <span><strong>{{ serverStats.replanned || replannedCount }}</strong>重规划</span>
          </div>
          <div v-if="statsOffline" class="offline-note">后端未连接，当前展示本地工作区数据</div>
        </div>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getFlywheelStats, getHardCases } from '@/services/api'
import { listWorkspaceRuns, openWorkspaceRun, type WorkspaceRun } from '@/services/workspace'

const router = useRouter()
const keyword = ref('')
const runs = ref<WorkspaceRun[]>([])
const hardCaseCount = ref(0)
const statsOffline = ref(false)
const serverStats = ref({ episodes: 0, feedback: 0, replanned: 0 })

const stages = [
  { name: '需求理解', desc: '抽取偏好与硬约束' },
  { name: '证据检索', desc: '融合资料与城市知识' },
  { name: '约束求解', desc: 'CP-SAT 生成可行日程' },
  { name: '结果校验', desc: '规则检查与自动修复' },
  { name: '反馈沉淀', desc: 'Trace、版本与难例归档' }
]

const filteredRuns = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  return query ? runs.value.filter(run => `${run.title}${run.request.city}`.toLowerCase().includes(query)) : runs.value
})
const validationRate = computed(() => runs.value.length ? Math.round(runs.value.filter(run => run.plan.validation_report?.passed !== false).length / runs.value.length * 100) : 0)
const averageScore = computed(() => {
  const scores = runs.value.map(run => run.plan.validation_report?.score).filter((score): score is number => typeof score === 'number')
  return scores.length ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length * 100) : 0
})
const feedbackCount = computed(() => runs.value.filter(run => run.feedback).length)
const replannedCount = computed(() => runs.value.filter(run => (run.plan.revision || 0) > 0).length)

const openRun = (run: WorkspaceRun) => {
  openWorkspaceRun(run)
  router.push('/result')
}
const formatTime = (value: string) => new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))

onMounted(async () => {
  runs.value = listWorkspaceRuns()
  try {
    const [stats, hardCases] = await Promise.all([getFlywheelStats(), getHardCases(100)])
    serverStats.value = {
      episodes: stats.episodes?.episodes || 0,
      feedback: stats.feedback?.total || 0,
      replanned: stats.episodes?.replanned_episodes || 0
    }
    hardCaseCount.value = hardCases.length
  } catch {
    statsOffline.value = true
    hardCaseCount.value = runs.value.filter(run => run.status === 'needs_review' || (run.plan.revision || 0) > 0).length
  }
})
</script>

<style scoped>
.workbench-page{max-width:1440px;margin:0 auto;padding:48px 42px 72px}.workbench-hero{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:32px}.eyebrow,.panel-kicker{font-size:11px;font-weight:800;letter-spacing:1.8px;color:#5e6b85}.live-dot{display:inline-block;width:7px;height:7px;margin-right:8px;border-radius:50%;background:#35c98a;box-shadow:0 0 0 5px rgba(53,201,138,.12)}h1{margin:10px 0 8px;font-family:var(--font-display);font-size:38px;letter-spacing:-1px;color:#10192d}.workbench-hero p{margin:0;color:#6e778a}.new-run-btn{height:46px;padding:0 22px;border:0;border-radius:10px;background:#e94560;box-shadow:0 9px 22px rgba(233,69,96,.22)}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:20px}.metric-card{display:flex;min-height:132px;flex-direction:column;padding:20px 22px;border:1px solid #e7eaf0;border-radius:14px;background:#fff;box-shadow:0 8px 28px rgba(20,31,55,.04)}.metric-card strong{margin:8px 0 5px;font-size:30px;color:#17213a}.metric-label{font-size:13px;font-weight:700;color:#59647a}.metric-note{font-size:12px;color:#98a0af}.accent-card{background:#17213a;border-color:#17213a}.accent-card strong,.accent-card .metric-label{color:#fff}.accent-card .metric-note{color:#9ca7bd}.workspace-grid{display:grid;grid-template-columns:minmax(0,1.7fr) minmax(330px,.75fr);gap:20px}.panel{border:1px solid #e7eaf0;border-radius:16px;background:#fff;box-shadow:0 10px 35px rgba(20,31,55,.05)}.panel-head{display:flex;justify-content:space-between;align-items:center;padding:22px 24px;border-bottom:1px solid #edf0f4}.panel-head.compact{border-bottom:0;padding-bottom:8px}.panel-head h2,.flywheel-title h2{margin:3px 0 0;font-size:17px;color:#19233b}.run-search{width:220px}.run-list{padding:8px}.run-row{display:grid;width:100%;grid-template-columns:12px minmax(190px,1fr) 150px 100px 20px;gap:14px;align-items:center;padding:17px 14px;border:0;border-bottom:1px solid #f0f2f5;background:#fff;text-align:left;cursor:pointer;transition:.2s}.run-row:last-child{border-bottom:0}.run-row:hover{border-radius:10px;background:#f7f9fc;transform:translateX(2px)}.run-status{width:8px;height:8px;border-radius:50%;background:#35c98a}.run-status.needs_review{background:#f3a33c}.run-status.failed{background:#e94560}.run-status.running{background:#4778ff}.run-main,.run-signals{display:flex;flex-direction:column;gap:5px}.run-main strong{color:#1c2740}.run-main small,.run-signals small,.run-time{font-size:12px;color:#8b94a6}.run-signals .ant-tag{width:max-content;margin:0}.row-arrow{color:#a2aaba;font-size:18px}.empty-runs{padding:70px 24px;text-align:center;color:#8790a2}.empty-mark{font-size:40px;color:#ccd2dc}.empty-runs h3{margin:12px 0 6px;color:#273249}.empty-runs p{margin-bottom:18px}.side-stack{display:flex;flex-direction:column;gap:20px}.pipeline{padding:4px 24px 20px}.pipeline-step{position:relative;display:grid;grid-template-columns:34px 1fr auto;gap:12px;align-items:center;padding:13px 0}.pipeline-step:not(:last-child):after{content:'';position:absolute;left:16px;top:42px;width:1px;height:22px;background:#dfe4ec}.stage-index{display:grid;width:32px;height:32px;place-items:center;border-radius:9px;background:#edf2ff;color:#315da8;font-size:11px;font-weight:800}.pipeline-step div{display:flex;flex-direction:column}.pipeline-step strong{font-size:13px;color:#24304a}.pipeline-step small{font-size:11px;color:#949cac}.stage-state{font-size:9px;font-weight:800;letter-spacing:.8px;color:#35a976}.flywheel-panel{padding:24px;background:linear-gradient(145deg,#152039,#202d4b);color:#fff}.flywheel-title{display:flex;gap:13px;align-items:center}.flywheel-title>span{display:grid;width:42px;height:42px;place-items:center;border-radius:12px;background:rgba(255,255,255,.09);font-size:24px}.flywheel-title small{font-size:9px;letter-spacing:1.5px;color:#91a0bf}.flywheel-title h2{color:#fff}.flywheel-panel>p{margin:18px 0;color:#b7c0d2;font-size:13px;line-height:1.8}.flywheel-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.flywheel-stats span{display:flex;flex-direction:column;padding:10px;border-radius:9px;background:rgba(255,255,255,.06);font-size:10px;color:#9faac0}.flywheel-stats strong{font-size:19px;color:#fff}.offline-note{margin-top:12px;font-size:11px;color:#f4c46c}@media(max-width:1000px){.metric-grid{grid-template-columns:repeat(2,1fr)}.workspace-grid{grid-template-columns:1fr}}@media(max-width:640px){.workbench-page{padding:28px 16px 50px}.workbench-hero{align-items:flex-start;flex-direction:column;gap:20px}.workbench-hero h1{font-size:30px}.metric-grid{grid-template-columns:1fr 1fr}.metric-card{min-height:112px;padding:16px}.run-row{grid-template-columns:10px 1fr 20px}.run-signals,.run-time{display:none}.panel-head{align-items:flex-start;flex-direction:column;gap:12px}.run-search{width:100%}}
</style>
