"use strict";

const translations = {
  ar: {
    pageTitle: "لوحة إدارة حكّاء التاريخ",
    brand: "حكّاء التاريخ",
    adminPanel: "لوحة الإدارة",
    openChat: "فتح واجهة الشات",
    openGrafana: "فتح Grafana",
    grafanaHint: "يتطلب تشغيل SSH Tunnel",

    sourceManagement: "إدارة المصادر والفهرسة",
    sourceDescription:
      "ارفع المصدر، ثم سيقوم النظام بمعالجته وتقسيمه وإنشاء الترميز وإضافته إلى فهرس البحث.",

    projectId: "رقم المشروع",
    refreshStatus: "تحديث الحالة",
    apiStatus: "حالة الـAPI",
    indexedRecords: "السجلات المفهرسة",
    operationStatus: "حالة العملية",

    checking: "جارٍ الفحص...",
    ready: "جاهز",
    connected: "متصل",
    running: "يعمل",
    unavailable: "غير متاح",
    disconnected: "غير متصل",
    operationRunning: "جارٍ التنفيذ",
    operationComplete: "اكتملت بنجاح",
    operationFailed: "فشلت العملية",

    addSource: "إضافة مصدر",
    uploadAndProcess: "رفع ومعالجة ملف",
    chooseSourceFile: "اختر ملف المصدر",
    clickToChoose: "اضغط لاختيار الملف",
    uploadHint: "الحد الأقصى للرفع 20MB. يتحقق الخادم من نوع الملف.",
    advancedSettings: "إعدادات التقسيم المتقدمة",
    chunkSize: "حجم الجزء",
    overlapSize: "حجم التداخل",
    resetWarning:
      "لن تستخدم الواجهة خيار Reset حفاظًا على البيانات الحالية.",
    startIngestion: "ابدأ الرفع والفهرسة",
    workingButton: "جارٍ تنفيذ العملية...",

    executionPath: "مسار التنفيذ",
    operationStages: "مراحل العملية",
    uploadFile: "رفع الملف",
    processText: "معالجة وتقسيم النص",
    createIndex: "إنشاء الترميز والفهرسة",
    verifyIndex: "التحقق من الفهرس",

    waitingToStart: "في انتظار البدء",
    waitingForUpload: "في انتظار الرفع",
    waitingForProcessing: "في انتظار المعالجة",
    waitingForIndexing: "في انتظار الفهرسة",

    operationLog: "سجل التشغيل",
    lastOperationDetails: "تفاصيل آخر عملية",
    clearView: "مسح العرض",
    adminReady: "لوحة الإدارة جاهزة.",

    selectFile: "اختر ملفًا أولًا",
    fileTooLarge: "حجم الملف يتجاوز 20MB",
    invalidChunk: "حجم الجزء غير صالح",
    invalidOverlap: "حجم التداخل يجب أن يكون أقل من حجم الجزء",
    invalidProject: "رقم المشروع يجب أن يكون رقمًا صحيحًا أكبر من صفر",

    uploading: "جارٍ رفع الملف...",
    uploadDone: "اكتمل رفع الملف",
    missingFileId: "نجح الرفع لكن لم يصل file_id من الخادم",

    processing: "جارٍ قراءة الملف وتقسيمه...",
    chunksCreated: "تم إنشاء {count} جزء",

    indexing: "جارٍ إنشاء الترميز وتحديث الفهرس...",
    indexingDone: "اكتملت الفهرسة: {count}",

    verifying: "جارٍ التحقق من عدد السجلات...",
    indexContains: "الفهرس يحتوي على {count} سجل",

    ingestionSuccess: "تم رفع المصدر وفهرسته بنجاح",
    displayCleared: "تم مسح سجل العرض.",

    logApiFailure: "فشل فحص API: {error}",
    logInfoFailure: "فشل قراءة معلومات الفهرس: {error}",
    logStart: "بدء معالجة الملف \"{file}\" للمشروع {project}",
    logUploadDone: "اكتمل رفع الملف",
    logProcessDone: "اكتملت معالجة الملف",
    logIndexDone: "اكتملت الفهرسة",
    logVerifyDone: "تم التحقق من الفهرس",
    logFailure: "فشلت العملية: {error}",

    fileDisplay: "{name} — {size} بايت",
    httpFailure: "فشل الطلب برمز HTTP {status}"
  },

  en: {
    pageTitle: "Hakkaa History Admin Dashboard",
    brand: "Hakkaa History",
    adminPanel: "Admin Dashboard",
    openChat: "Open Chat",
    openGrafana: "Open Grafana",
    grafanaHint: "Requires an active SSH tunnel",

    sourceManagement: "Sources and Index Management",
    sourceDescription:
      "Upload a source and the system will process, chunk, embed, and add it to the search index.",

    projectId: "Project ID",
    refreshStatus: "Refresh Status",
    apiStatus: "API Status",
    indexedRecords: "Indexed Records",
    operationStatus: "Operation Status",

    checking: "Checking...",
    ready: "Ready",
    connected: "Connected",
    running: "Running",
    unavailable: "Unavailable",
    disconnected: "Disconnected",
    operationRunning: "Processing",
    operationComplete: "Completed Successfully",
    operationFailed: "Operation Failed",

    addSource: "Add Source",
    uploadAndProcess: "Upload and Process File",
    chooseSourceFile: "Choose Source File",
    clickToChoose: "Click to choose a file",
    uploadHint: "Maximum upload size is 20MB. The server validates the file type.",
    advancedSettings: "Advanced Chunking Settings",
    chunkSize: "Chunk Size",
    overlapSize: "Overlap Size",
    resetWarning:
      "The Reset option is disabled to protect the existing data.",
    startIngestion: "Start Upload and Indexing",
    workingButton: "Processing...",

    executionPath: "Execution Pipeline",
    operationStages: "Operation Stages",
    uploadFile: "Upload File",
    processText: "Process and Chunk Text",
    createIndex: "Create Embeddings and Index",
    verifyIndex: "Verify Index",

    waitingToStart: "Waiting to start",
    waitingForUpload: "Waiting for upload",
    waitingForProcessing: "Waiting for processing",
    waitingForIndexing: "Waiting for indexing",

    operationLog: "Operation Log",
    lastOperationDetails: "Latest Operation Details",
    clearView: "Clear View",
    adminReady: "Admin dashboard is ready.",

    selectFile: "Choose a file first",
    fileTooLarge: "The file exceeds the 20MB limit",
    invalidChunk: "The chunk size is invalid",
    invalidOverlap: "Overlap size must be smaller than chunk size",
    invalidProject: "Project ID must be a positive integer",

    uploading: "Uploading the file...",
    uploadDone: "File upload completed",
    missingFileId: "Upload succeeded but the server did not return file_id",

    processing: "Reading and chunking the file...",
    chunksCreated: "Created {count} chunks",

    indexing: "Creating embeddings and updating the index...",
    indexingDone: "Indexing completed: {count}",

    verifying: "Verifying the indexed records...",
    indexContains: "The index contains {count} records",

    ingestionSuccess: "The source was uploaded and indexed successfully",
    displayCleared: "The displayed log was cleared.",

    logApiFailure: "API check failed: {error}",
    logInfoFailure: "Failed to retrieve index information: {error}",
    logStart: "Started processing \"{file}\" for project {project}",
    logUploadDone: "File upload completed",
    logProcessDone: "File processing completed",
    logIndexDone: "Indexing completed",
    logVerifyDone: "Index verification completed",
    logFailure: "Operation failed: {error}",

    fileDisplay: "{name} — {size} bytes",
    httpFailure: "Request failed with HTTP status {status}"
  }
};


const elements = {
  languageToggle: document.querySelector("#languageToggle"),
  grafanaLink: document.querySelector("#grafanaLink"),

  projectId: document.querySelector("#projectId"),
  refreshStatus: document.querySelector("#refreshStatus"),

  apiState: document.querySelector("#apiState"),
  recordCount: document.querySelector("#recordCount"),
  jobState: document.querySelector("#jobState"),

  form: document.querySelector("#ingestForm"),
  fileInput: document.querySelector("#fileInput"),
  selectedFileName: document.querySelector("#selectedFileName"),
  chunkSize: document.querySelector("#chunkSize"),
  overlapSize: document.querySelector("#overlapSize"),
  ingestButton: document.querySelector("#ingestButton"),

  pipeline: document.querySelector("#pipeline"),
  eventLog: document.querySelector("#eventLog"),
  clearLog: document.querySelector("#clearLog"),
  toast: document.querySelector("#toast")
};


let currentLanguage =
  localStorage.getItem("adminLanguage") === "en" ? "en" : "ar";

let currentStep = null;
let toastTimer = null;


function t(key, values = {}) {
  let text =
    translations[currentLanguage][key] ??
    translations.ar[key] ??
    key;

  for (const [name, value] of Object.entries(values)) {
    text = text.replaceAll(`{${name}}`, String(value));
  }

  return text;
}


function formatNumber(value) {
  const locale = currentLanguage === "ar" ? "ar-EG" : "en-US";
  return new Intl.NumberFormat(locale).format(value);
}


function applyLanguage() {
  document.documentElement.lang = currentLanguage;
  document.documentElement.dir =
    currentLanguage === "ar" ? "rtl" : "ltr";

  document.querySelectorAll("[data-i18n]").forEach(element => {
    element.textContent = t(element.dataset.i18n);
  });

  document
    .querySelectorAll("[data-i18n-title]")
    .forEach(element => {
      element.title = t(element.dataset.i18nTitle);
    });

  elements.languageToggle.textContent =
    currentLanguage === "ar" ? "English" : "العربية";
}


function getProjectId() {
  const projectId = Number(elements.projectId.value);

  if (!Number.isInteger(projectId) || projectId < 1) {
    throw new Error(t("invalidProject"));
  }

  return projectId;
}


function setStatus(element, text, className = "") {
  element.textContent = text;

  element.classList.remove(
    "status-online",
    "status-offline",
    "status-working"
  );

  if (className) {
    element.classList.add(className);
  }
}


function setJobState(text, className = "") {
  setStatus(elements.jobState, text, className);
}


function writeLog(message, data = null) {
  const locale = currentLanguage === "ar" ? "ar-EG" : "en-US";

  const time = new Intl.DateTimeFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  }).format(new Date());

  let line = `[${time}] ${message}`;

  if (data !== null) {
    line += `\n${JSON.stringify(data, null, 2)}`;
  }

  elements.eventLog.textContent += `\n${line}`;
  elements.eventLog.scrollTop =
    elements.eventLog.scrollHeight;
}


function showToast(message, type = "success") {
  clearTimeout(toastTimer);

  elements.toast.textContent = message;
  elements.toast.className = `${type} show`;

  toastTimer = setTimeout(() => {
    elements.toast.className = "";
  }, 4500);
}


function resetPipeline() {
  const messages = {
    upload: "waitingToStart",
    process: "waitingForUpload",
    index: "waitingForProcessing",
    verify: "waitingForIndexing"
  };

  currentStep = null;

  for (const [stepName, translationKey] of Object.entries(messages)) {
    const step = elements.pipeline.querySelector(
      `[data-step="${stepName}"]`
    );

    step.classList.remove(
      "is-active",
      "is-success",
      "is-error"
    );

    step.querySelector("small").textContent =
      t(translationKey);
  }
}


function setStep(stepName, state, message) {
  const step = elements.pipeline.querySelector(
    `[data-step="${stepName}"]`
  );

  if (!step) return;

  step.classList.remove(
    "is-active",
    "is-success",
    "is-error"
  );

  if (state) {
    step.classList.add(`is-${state}`);
  }

  step.querySelector("small").textContent = message;
  currentStep = stepName;
}


function setBusy(isBusy) {
  elements.ingestButton.disabled = isBusy;
  elements.fileInput.disabled = isBusy;
  elements.chunkSize.disabled = isBusy;
  elements.overlapSize.disabled = isBusy;
  elements.projectId.disabled = isBusy;
  elements.refreshStatus.disabled = isBusy;
  elements.languageToggle.disabled = isBusy;

  elements.ingestButton.textContent =
    isBusy ? t("workingButton") : t("startIngestion");
}


function errorMessage(payload, status) {
  if (typeof payload === "string" && payload.trim()) {
    return payload;
  }

  if (Array.isArray(payload?.detail)) {
    return payload.detail
      .map(item => item.msg || JSON.stringify(item))
      .join(", ");
  }

  const reason =
    payload?.detail ||
    payload?.signal ||
    payload?.message;

  if (reason) {
    return typeof reason === "string"
      ? reason
      : JSON.stringify(reason);
  }

  return t("httpFailure", { status });
}


async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options
  });

  const rawBody = await response.text();
  let payload = null;

  if (rawBody) {
    try {
      payload = JSON.parse(rawBody);
    } catch {
      payload = rawBody;
    }
  }

  if (!response.ok) {
    throw new Error(errorMessage(payload, response.status));
  }

  return payload;
}


async function refreshDashboard() {
  let projectId;

  try {
    projectId = getProjectId();
  } catch (error) {
    showToast(error.message, "error");
    return;
  }

  elements.refreshStatus.disabled = true;

  setStatus(
    elements.apiState,
    t("checking"),
    "status-working"
  );

  try {
    const health = await requestJson("/api/v1/");

    setStatus(
      elements.apiState,
      health?.app_name ? t("connected") : t("running"),
      "status-online"
    );
  } catch (error) {
    setStatus(
      elements.apiState,
      t("disconnected"),
      "status-offline"
    );

    writeLog(
      t("logApiFailure", { error: error.message })
    );
  }

  try {
    const info = await requestJson(
      `/api/v1/nlp/index/info/${projectId}`
    );

    elements.recordCount.textContent =
      formatNumber(Number(info?.record_count || 0));
  } catch (error) {
    elements.recordCount.textContent = t("unavailable");

    writeLog(
      t("logInfoFailure", { error: error.message })
    );
  } finally {
    elements.refreshStatus.disabled = false;
  }
}


async function runIngestion(event) {
  event.preventDefault();

  const file = elements.fileInput.files[0];

  if (!file) {
    showToast(t("selectFile"), "error");
    return;
  }

  if (file.size > 20 * 1024 * 1024) {
    showToast(t("fileTooLarge"), "error");
    return;
  }

  const chunkSize = Number(elements.chunkSize.value);
  const overlapSize = Number(elements.overlapSize.value);

  if (!Number.isInteger(chunkSize) || chunkSize < 1) {
    showToast(t("invalidChunk"), "error");
    return;
  }

  if (
    !Number.isInteger(overlapSize) ||
    overlapSize < 0 ||
    overlapSize >= chunkSize
  ) {
    showToast(t("invalidOverlap"), "error");
    return;
  }

  let projectId;

  try {
    projectId = getProjectId();
  } catch (error) {
    showToast(error.message, "error");
    return;
  }

  localStorage.setItem(
    "adminProjectId",
    String(projectId)
  );

  resetPipeline();
  setBusy(true);

  setJobState(
    t("operationRunning"),
    "status-working"
  );

  writeLog(
    t("logStart", {
      file: file.name,
      project: projectId
    })
  );

  try {
    currentStep = "upload";
    setStep("upload", "active", t("uploading"));

    const uploadBody = new FormData();
    uploadBody.append("file", file);

    const uploadResult = await requestJson(
      `/api/v1/data/upload/${projectId}`,
      {
        method: "POST",
        body: uploadBody
      }
    );

    const fileId = uploadResult?.file_id;

    if (!fileId) {
      throw new Error(t("missingFileId"));
    }

    setStep("upload", "success", t("uploadDone"));
    writeLog(t("logUploadDone"), uploadResult);


    currentStep = "process";
    setStep("process", "active", t("processing"));

    const processResult = await requestJson(
      `/api/v1/data/process/${projectId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          file_id: fileId,
          chunk_size: chunkSize,
          overlap_size: overlapSize,
          do_reset: 0
        })
      }
    );

    setStep(
      "process",
      "success",
      t("chunksCreated", {
        count: formatNumber(
          processResult?.inserted_chunks ?? 0
        )
      })
    );

    writeLog(t("logProcessDone"), processResult);


    currentStep = "index";
    setStep("index", "active", t("indexing"));

    const indexResult = await requestJson(
      `/api/v1/nlp/index/push/${projectId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          do_reset: 0
        })
      }
    );

    const indexedCount =
      indexResult?.inserted_item_count ??
      indexResult?.inseerted_item_count ??
      t("unavailable");

    setStep(
      "index",
      "success",
      t("indexingDone", {
        count:
          typeof indexedCount === "number"
            ? formatNumber(indexedCount)
            : indexedCount
      })
    );

    writeLog(t("logIndexDone"), indexResult);


    currentStep = "verify";
    setStep("verify", "active", t("verifying"));

    const infoResult = await requestJson(
      `/api/v1/nlp/index/info/${projectId}`
    );

    const totalRecords = Number(
      infoResult?.record_count || 0
    );

    elements.recordCount.textContent =
      formatNumber(totalRecords);

    setStep(
      "verify",
      "success",
      t("indexContains", {
        count: formatNumber(totalRecords)
      })
    );

    writeLog(t("logVerifyDone"), infoResult);

    setJobState(
      t("operationComplete"),
      "status-online"
    );

    showToast(t("ingestionSuccess"), "success");

    elements.form.reset();
    elements.selectedFileName.textContent =
      t("clickToChoose");
  } catch (error) {
    if (currentStep) {
      setStep(
        currentStep,
        "error",
        error.message
      );
    }

    setJobState(
      t("operationFailed"),
      "status-offline"
    );

    writeLog(
      t("logFailure", { error: error.message })
    );

    showToast(error.message, "error");
  } finally {
    setBusy(false);
  }
}


elements.languageToggle.addEventListener("click", () => {
  const nextLanguage =
    currentLanguage === "ar" ? "en" : "ar";

  localStorage.setItem(
    "adminLanguage",
    nextLanguage
  );

  window.location.reload();
});


elements.fileInput.addEventListener("change", () => {
  const file = elements.fileInput.files[0];

  elements.selectedFileName.textContent = file
    ? t("fileDisplay", {
        name: file.name,
        size: formatNumber(file.size)
      })
    : t("clickToChoose");
});


elements.refreshStatus.addEventListener(
  "click",
  refreshDashboard
);


elements.clearLog.addEventListener("click", () => {
  elements.eventLog.textContent = t("displayCleared");
});


elements.projectId.addEventListener("change", () => {
  const projectId = Number(elements.projectId.value);

  if (Number.isInteger(projectId) && projectId > 0) {
    localStorage.setItem(
      "adminProjectId",
      String(projectId)
    );

    refreshDashboard();
  }
});


elements.form.addEventListener(
  "submit",
  runIngestion
);


const savedProjectId = Number(
  localStorage.getItem("adminProjectId")
);

if (
  Number.isInteger(savedProjectId) &&
  savedProjectId > 0
) {
  elements.projectId.value = savedProjectId;
}

applyLanguage();
resetPipeline();
refreshDashboard();