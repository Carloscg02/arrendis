📱 Feature Futura: Aplicación Móvil (React Native)Estado: 💡 IDEA / BACKLOGPúblico Objetivo de este documento: Tech Lead Humano y Agentes de IAEnfoque Arquitectónico:

Nivel 2 - UI Nativa con Lógica de Negocio Compartida1. Contexto y EstrategiaEste documento describe la estrategia para construir una aplicación móvil nativa (iOS y Android) para el sistema de Gestión de Alquileres.Dado que el backend está construido usando Arquitectura Hexagonal y expuesto a través de una FastAPI RESTful, el backend permanecerá 100% intacto. La app móvil actuará como un nuevo "Adaptador de Entrada" (exactamente igual que la SPA web actual en React).Usaremos React Native (vía Expo). Esto nos permite reutilizar nuestro conocimiento actual de React y TypeScript, y compartir estrictamente la capa de comunicación con la API de nuestro proyecto web.2. Directivas Principales para Agentes de IAAl implementar esta feature, el Agente de IA DEBE adherirse a las siguientes reglas:

REGLA 1: El Backend es Sagrado. No modifiques nada dentro de los directorios backend/ o tests/. La API es la única fuente de la verdad.

REGLA 2: Porta, no reinventes. La capa de servicios de la API y los tipos de TypeScript del frontend web DEBEN reutilizarse. No escribas nueva lógica para las peticiones HTTP.

REGLA 3: Solo Componentes Nativos. NO utilices etiquetas web (<div>, <span>) ni Vanilla CSS. Debes usar los componentes de React Native (<View>, <Text>) y StyleSheet.3. Hoja de Ruta de ImplementaciónPaso 1: InicializaciónInicializar un nuevo proyecto Expo en un nuevo directorio en la raíz: npx create-expo-app mobile --template expo-template-blank-typescriptAsegurar que la estructura de directorios se sitúe junto al frontend web:/rental-core
├── backend/     (Python/FastAPI - Intocable)
├── frontend/    (React Web SPA - Solo referencia)
└── mobile/      (Nueva app React Native Expo)

Paso 2: Migración de Lógica CompartidaCopiar frontend/src/types/index.ts a mobile/src/types/index.ts.Copiar frontend/src/services/api.ts a mobile/src/services/api.ts.Nota: Ajustar la URL API_BASE en la app móvil (ej. 10.0.2.2 para el emulador de Android o la IP de la red local en lugar de localhost).

Paso 3: Configuración de NavegaciónInstalar React Navigation (@react-navigation/native y @react-navigation/native-stack).Implementar el enrutamiento equivalente a la app web (ej. pantallas PropertyList y PropertyDetail).Paso 4: Implementación de la UITraducir la UI Web a UI Móvil.Reemplazar las tarjetas web estándar por tarjetas de React Native o componentes <View> estilizados.Asegurar que la UX sea amigable para móviles (ej. áreas táctiles suficientemente grandes, uso de modales nativos para formularios).

4. Prompt de IA sugerido para iniciar esta featureCopia y pega lo siguiente a la IA cuando estés listo para empezar:"Vamos a empezar la implementación de la App Móvil para este proyecto. Por favor, lee las especificaciones en docs/future_ideas/mobile_app_migration.md.Empieza ejecutando el Paso 1 (Inicialización) y el Paso 2 (Lógica Compartida). No construyas la UI todavía. Confirma una vez que el proyecto Expo esté creado y los tipos/servicios se hayan copiado con éxito."