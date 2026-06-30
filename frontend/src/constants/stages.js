/**
 * 业务流程阶段定义
 * 用于在导入 / 导出 / 筛选 / 更新等场景中标识当前步骤
 */

export const STAGE = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  VALIDATING: 'validating',
  PREVIEWING: 'previewing',
  CONFIRMING: 'confirming',
  IMPORTING: 'importing',
  EXPORTING: 'exporting',
  UPDATING: 'updating',
  SUCCESS: 'success',
  FAILED: 'failed'
}

// 阶段文案映射
export const STAGE_TEXT = {
  [STAGE.IDLE]: '待开始',
  [STAGE.UPLOADING]: '上传中',
  [STAGE.VALIDATING]: '校验中',
  [STAGE.PREVIEWING]: '预览中',
  [STAGE.CONFIRMING]: '等待确认',
  [STAGE.IMPORTING]: '导入中',
  [STAGE.EXPORTING]: '导出中',
  [STAGE.UPDATING]: '更新中',
  [STAGE.SUCCESS]: '完成',
  [STAGE.FAILED]: '失败'
}

// 阶段状态颜色（Element Plus tag type）
export const STAGE_TAG_TYPE = {
  [STAGE.IDLE]: 'info',
  [STAGE.UPLOADING]: 'warning',
  [STAGE.VALIDATING]: 'warning',
  [STAGE.PREVIEWING]: '',
  [STAGE.CONFIRMING]: '',
  [STAGE.IMPORTING]: 'warning',
  [STAGE.EXPORTING]: 'warning',
  [STAGE.UPDATING]: 'warning',
  [STAGE.SUCCESS]: 'success',
  [STAGE.FAILED]: 'danger'
}

export default {
  STAGE,
  STAGE_TEXT,
  STAGE_TAG_TYPE
}
