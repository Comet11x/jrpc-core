import { defineConfig } from "vitepress"

export default defineConfig({
  title: "jrpc-core",
  description: "JSON-RPC 2.0 for Python — messages, dispatching, and validation.",
  srcDir: "src",
  outDir: "dist",
  // base: "https://comet11x.github.io/jrpc-core/",

  locales: {
    root: {
      label: "English",
      lang: "en",
      themeConfig: {
        nav: [
          { text: "Guide", link: "/guide/", activeMatch: "/guide/" },
          { text: "Messages API", link: "/guide/messages", activeMatch: "/guide/messages" },
          { text: "Dispatcher API", link: "/guide/dispatcher", activeMatch: "/guide/dispatcher" },
        ],
        sidebar: [
          {
            text: "Introduction",
            items: [
              { text: "What is jrpc-core?", link: "/guide/" },
              { text: "Getting Started", link: "/guide/getting-started" },
            ],
          },
          {
            text: "API Reference",
            items: [
              { text: "Messages", link: "/guide/messages" },
              { text: "Dispatcher", link: "/guide/dispatcher" },
            ],
          },
        ],
      },
    },
    ru: {
      label: "Русский",
      lang: "ru",
      themeConfig: {
        nav: [
          { text: "Руководство", link: "/ru/guide/", activeMatch: "/ru/guide/" },
          { text: "API сообщений", link: "/ru/guide/messages", activeMatch: "/ru/guide/messages" },
          { text: "API диспетчера", link: "/ru/guide/dispatcher", activeMatch: "/ru/guide/dispatcher" },
        ],
        sidebar: [
          {
            text: "Введение",
            items: [
              { text: "Что такое jrpc-core?", link: "/ru/guide/" },
              { text: "Начало работы", link: "/ru/guide/getting-started" },
            ],
          },
          {
            text: "Справочник API",
            items: [
              { text: "Сообщения", link: "/ru/guide/messages" },
              { text: "Диспетчер", link: "/ru/guide/dispatcher" },
            ],
          },
        ],
      },
    },
    zh: {
      label: "简体中文",
      lang: "zh-Hans",
      themeConfig: {
        nav: [
          { text: "指南", link: "/zh/guide/", activeMatch: "/zh/guide/" },
          { text: "消息 API", link: "/zh/guide/messages", activeMatch: "/zh/guide/messages" },
          { text: "调度器 API", link: "/zh/guide/dispatcher", activeMatch: "/zh/guide/dispatcher" },
        ],
        sidebar: [
          {
            text: "介绍",
            items: [
              { text: "什么是 jrpc-core？", link: "/zh/guide/" },
              { text: "快速开始", link: "/zh/guide/getting-started" },
            ],
          },
          {
            text: "API 参考",
            items: [
              { text: "消息", link: "/zh/guide/messages" },
              { text: "调度器", link: "/zh/guide/dispatcher" },
            ],
          },
        ],
      },
    },
    de: {
      label: "Deutsch",
      lang: "de",
      themeConfig: {
        nav: [
          { text: "Handbuch", link: "/de/guide/", activeMatch: "/de/guide/" },
          { text: "Nachrichten-API", link: "/de/guide/messages", activeMatch: "/de/guide/messages" },
          { text: "Dispatcher-API", link: "/de/guide/dispatcher", activeMatch: "/de/guide/dispatcher" },
        ],
        sidebar: [
          {
            text: "Einführung",
            items: [
              { text: "Was ist jrpc-core?", link: "/de/guide/" },
              { text: "Erste Schritte", link: "/de/guide/getting-started" },
            ],
          },
          {
            text: "API-Referenz",
            items: [
              { text: "Nachrichten", link: "/de/guide/messages" },
              { text: "Dispatcher", link: "/de/guide/dispatcher" },
            ],
          },
        ],
      },
    },
    it: {
      label: "Italiano",
      lang: "it",
      themeConfig: {
        nav: [
          { text: "Guida", link: "/it/guide/", activeMatch: "/it/guide/" },
          { text: "API Messaggi", link: "/it/guide/messages", activeMatch: "/it/guide/messages" },
          { text: "API Dispatcher", link: "/it/guide/dispatcher", activeMatch: "/it/guide/dispatcher" },
        ],
        sidebar: [
          {
            text: "Introduzione",
            items: [
              { text: "Cos'è jrpc-core?", link: "/it/guide/" },
              { text: "Per Iniziare", link: "/it/guide/getting-started" },
            ],
          },
          {
            text: "Riferimento API",
            items: [
              { text: "Messaggi", link: "/it/guide/messages" },
              { text: "Dispatcher", link: "/it/guide/dispatcher" },
            ],
          },
        ],
      },
    },
    fr: {
      label: "Français",
      lang: "fr",
      themeConfig: {
        nav: [
          { text: "Guide", link: "/fr/guide/", activeMatch: "/fr/guide/" },
          { text: "API Messages", link: "/fr/guide/messages", activeMatch: "/fr/guide/messages" },
          { text: "API Dispatcher", link: "/fr/guide/dispatcher", activeMatch: "/fr/guide/dispatcher" },
        ],
        sidebar: [
          {
            text: "Introduction",
            items: [
              { text: "Qu'est-ce que jrpc-core ?", link: "/fr/guide/" },
              { text: "Pour Commencer", link: "/fr/guide/getting-started" },
            ],
          },
          {
            text: "Référence API",
            items: [
              { text: "Messages", link: "/fr/guide/messages" },
              { text: "Dispatcher", link: "/fr/guide/dispatcher" },
            ],
          },
        ],
      },
    },
    pt: {
      label: "Português",
      lang: "pt",
      themeConfig: {
        nav: [
          { text: "Guia", link: "/pt/guide/", activeMatch: "/pt/guide/" },
          { text: "API de Mensagens", link: "/pt/guide/messages", activeMatch: "/pt/guide/messages" },
          { text: "API de Dispatcher", link: "/pt/guide/dispatcher", activeMatch: "/pt/guide/dispatcher" },
        ],
        sidebar: [
          {
            text: "Introdução",
            items: [
              { text: "O que é jrpc-core?", link: "/pt/guide/" },
              { text: "Primeiros Passos", link: "/pt/guide/getting-started" },
            ],
          },
          {
            text: "Referência da API",
            items: [
              { text: "Mensagens", link: "/pt/guide/messages" },
              { text: "Dispatcher", link: "/pt/guide/dispatcher" },
            ],
          },
        ],
      },
    },
    ko: {
      label: "한국어",
      lang: "ko",
      themeConfig: {
        nav: [
          { text: "가이드", link: "/ko/guide/", activeMatch: "/ko/guide/" },
          { text: "메시지 API", link: "/ko/guide/messages", activeMatch: "/ko/guide/messages" },
          { text: "디스패처 API", link: "/ko/guide/dispatcher", activeMatch: "/ko/guide/dispatcher" },
        ],
        sidebar: [
          {
            text: "소개",
            items: [
              { text: "jrpc-core란?", link: "/ko/guide/" },
              { text: "시작하기", link: "/ko/guide/getting-started" },
            ],
          },
          {
            text: "API 레퍼런스",
            items: [
              { text: "메시지", link: "/ko/guide/messages" },
              { text: "디스패처", link: "/ko/guide/dispatcher" },
            ],
          },
        ],
      },
    },
    ja: {
      label: "日本語",
      lang: "ja",
      themeConfig: {
        nav: [
          { text: "ガイド", link: "/ja/guide/", activeMatch: "/ja/guide/" },
          { text: "メッセージ API", link: "/ja/guide/messages", activeMatch: "/ja/guide/messages" },
          { text: "ディスパッチャ API", link: "/ja/guide/dispatcher", activeMatch: "/ja/guide/dispatcher" },
        ],
        sidebar: [
          {
            text: "はじめに",
            items: [
              { text: "jrpc-core とは？", link: "/ja/guide/" },
              { text: "セットアップ", link: "/ja/guide/getting-started" },
            ],
          },
          {
            text: "API リファレンス",
            items: [
              { text: "メッセージ", link: "/ja/guide/messages" },
              { text: "ディスパッチャ", link: "/ja/guide/dispatcher" },
            ],
          },
        ],
      },
    },
    es: {
      label: "Español",
      lang: "es",
      themeConfig: {
        nav: [
          { text: "Guía", link: "/es/guide/", activeMatch: "/es/guide/" },
          { text: "API de Mensajes", link: "/es/guide/messages", activeMatch: "/es/guide/messages" },
          { text: "API de Dispatcher", link: "/es/guide/dispatcher", activeMatch: "/es/guide/dispatcher" },
        ],
        sidebar: [
          {
            text: "Introducción",
            items: [
              { text: "¿Qué es jrpc-core?", link: "/es/guide/" },
              { text: "Primeros Pasos", link: "/es/guide/getting-started" },
            ],
          },
          {
            text: "Referencia de la API",
            items: [
              { text: "Mensajes", link: "/es/guide/messages" },
              { text: "Dispatcher", link: "/es/guide/dispatcher" },
            ],
          },
        ],
      },
    },
  },

  head: [
    [
      "link",
      {
        rel: "stylesheet",
        href: "https://cdn.jsdelivr.net/npm/@mdi/font@7.4.47/css/materialdesignicons.min.css",
      },
    ],
  ],

  themeConfig: {
    socialLinks: [
      { icon: "github", link: "https://github.com/comet11x/jrpc-core" },
    ],
  },
})
