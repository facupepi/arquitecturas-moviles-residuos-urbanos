// Reglas de roles por correo de Google, probadas en el emulador (no se pueden automatizar con cuentas reales de Google).
const { initializeTestEnvironment, assertSucceeds, assertFails } = require('@firebase/rules-unit-testing');
const fs = require('fs'), path = require('path');
const google = (email, verificado = true, proveedor = 'google.com') => ({ email, email_verified: verificado, firebase: { sign_in_provider: proveedor } });
let ok = 0, total = 0;
async function chk(nombre, promesa) { total++; try { await promesa; ok++; console.log('OK   ', nombre); } catch (e) { console.log('FALLA', nombre, String(e.message).slice(0, 90)); } }

(async () => {
  const env = await initializeTestEnvironment({ projectId: 'demo-residuos',
    firestore: { rules: fs.readFileSync(path.join(__dirname, '../../infraestructura/firestore.rules'), 'utf8') } });
  await env.withSecurityRulesDisabled(async (c) => {
    const db = c.firestore();
    await db.doc('roles_por_correo/jefe@ejemplo.invalid').set({ rol: 'autoridad' });
    await db.doc('roles_por_correo/chofer@ejemplo.invalid').set({ rol: 'recolector' });
    await db.doc('solicitudes_residuos/s1').set({ usuarioId: 'otro', estado: 'pendiente', tipoResiduo: 'voluminoso', direccion: 'Calle 12345', fechaCreacion: new Date() });
    await db.doc('solicitudes_residuos/s3').set({ solicitudId: 'SOL-SF-300', usuarioId: 'u3', estado: 'pendiente', tipoResiduo: 'voluminoso', direccion: 'Calle 12345', fechaCreacion: new Date() });
    await db.doc('incidentes/i1').set({ incidenteId: 'INC-SF-100', tipo: 'Contenedor roto', ubicacion: 'Calle 1', gravedad: 'media', estado: 'abierto', creadoPor: 'u3' });
    await db.doc('dispositivos/tok-vecino').set({ uid: 'u3', rol: 'ciudadano', actualizado: new Date() });
    await db.doc('telemetria_contenedores/ECO-SF-001').set({ porcentajeLlenado: 90, alertaDesborde: true });
    await db.doc('solicitudes_residuos/s3').set({ solicitudId: 'SOL-SF-300', usuarioId: 'u3', estado: 'pendiente', tipoResiduo: 'voluminoso', direccion: 'Calle 12345', fechaCreacion: new Date() });
    await db.doc('incidentes/i1').set({ incidenteId: 'INC-SF-100', tipo: 'Contenedor roto', ubicacion: 'Calle 1', gravedad: 'media', estado: 'abierto', creadoPor: 'u3' });
    await db.doc('dispositivos/tok-vecino').set({ uid: 'u3', rol: 'ciudadano', actualizado: new Date() });
    await db.doc('telemetria_contenedores/ECO-SF-001').set({ porcentajeLlenado: 90, alertaDesborde: true });
  });
  const jefe = env.authenticatedContext('u1', google('jefe@ejemplo.invalid')).firestore();
  const chofer = env.authenticatedContext('u2', google('chofer@ejemplo.invalid')).firestore();
  const vecino = env.authenticatedContext('u3', google('vecino@ejemplo.invalid')).firestore();
  const sinVerificar = env.authenticatedContext('u4', google('jefe@ejemplo.invalid', false)).firestore();
  const clave = env.authenticatedContext('u5', google('jefe@ejemplo.invalid', true, 'password')).firestore();
  const anonimo = env.unauthenticatedContext().firestore();

  await chk('Autoridad por correo lee todas las solicitudes', assertSucceeds(jefe.collection('solicitudes_residuos').get()));
  await chk('Autoridad por correo difunde una campaña', assertSucceeds(jefe.doc('notificaciones/n1').set({ titulo: 'x' })));
  await chk('Autoridad por correo publica telemetría', assertSucceeds(jefe.doc('telemetria_contenedores/t1').set({ porcentajeLlenado: 40 })));
  await chk('Cuadrilla por correo lee las solicitudes', assertSucceeds(chofer.collection('solicitudes_residuos').get()));
  await chk('Cuadrilla por correo no difunde campañas', assertFails(chofer.doc('notificaciones/n2').set({ titulo: 'x' })));
  await chk('Cuenta de Google sin rol no lee las solicitudes ajenas', assertFails(vecino.collection('solicitudes_residuos').get()));
  await chk('Cuenta sin rol no difunde campañas', assertFails(vecino.doc('notificaciones/n3').set({ titulo: 'x' })));
  await chk('Correo sin verificar no obtiene el rol', assertFails(sinVerificar.collection('solicitudes_residuos').get()));
  await chk('Ingreso con clave (no Google) no obtiene el rol', assertFails(clave.collection('solicitudes_residuos').get()));
  await chk('Anónimo no lee las solicitudes', assertFails(anonimo.collection('solicitudes_residuos').get()));
  await chk('Cada persona lee su propio rol', assertSucceeds(jefe.doc('roles_por_correo/jefe@ejemplo.invalid').get()));
  await chk('Nadie lee el rol de otra persona', assertFails(vecino.doc('roles_por_correo/jefe@ejemplo.invalid').get()));
  await chk('Nadie lista los roles', assertFails(jefe.collection('roles_por_correo').get()));
  await chk('Nadie se asigna un rol', assertFails(vecino.doc('roles_por_correo/vecino@ejemplo.invalid').set({ rol: 'autoridad' })));
  await chk('Ni siquiera la autoridad escribe roles', assertFails(jefe.doc('roles_por_correo/otro@ejemplo.invalid').set({ rol: 'autoridad' })));
  const sol = (extra = {}) => ({ solicitudId: 'SOL-SF-123456', usuarioId: 'u3', estado: 'pendiente', tipoResiduo: 'voluminoso',
    direccion: 'Bv. 25 de Mayo 1420', fechaCreacion: new Date(), ...extra });
  const inc = (extra = {}) => ({ incidenteId: 'INC-SF-123456', tipo: 'Contenedor roto', ubicacion: 'Calle 1', gravedad: 'alta',
    estado: 'abierto', creadoPor: 'u3', ...extra });
  await chk('Vecino crea una solicitud válida', assertSucceeds(vecino.doc('solicitudes_residuos/n1').set(sol())));
  await chk('Vecino no crea una solicitud con código inválido', assertFails(vecino.doc('solicitudes_residuos/n2').set(sol({ solicitudId: "SOL-');alert(1)//" }))));
  await chk('Vecino no crea una solicitud con campos extra', assertFails(vecino.doc('solicitudes_residuos/n3').set(sol({ cuadrilla: 'Móvil 03' }))));
  await chk('Vecino no marca como retirada su solicitud', assertFails(vecino.doc('solicitudes_residuos/s3').update({ estado: 'recolectado' })));
  await chk('Vecino no se asigna una cuadrilla', assertFails(vecino.doc('solicitudes_residuos/s3').update({ estado: 'en_camino', cuadrilla: 'Móvil 03' })));
  await chk('Vecino cancela su solicitud pendiente', assertSucceeds(vecino.doc('solicitudes_residuos/s3').update({ estado: 'cancelado' })));
  await chk('Cuadrilla confirma con peso y ubicación', assertSucceeds(chofer.doc('solicitudes_residuos/s1').update({ estado: 'recolectado', pesoRealKg: 12, geocerca: 'fuera', distanciaM: 80, observacionesRecoleccion: 'Bolsas rotas' })));
  await chk('Cuadrilla no cambia la dirección', assertFails(chofer.doc('solicitudes_residuos/s1').update({ direccion: 'Otra 1234' })));
  await chk('Vecino crea un incidente válido', assertSucceeds(vecino.doc('incidentes/n1').set(inc())));
  await chk('Vecino no crea un incidente con gravedad inventada', assertFails(vecino.doc('incidentes/n2').set(inc({ gravedad: '<b>x</b>' }))));
  await chk('Vecino no crea un incidente a nombre de otro', assertFails(vecino.doc('incidentes/n3').set(inc({ creadoPor: 'otro' }))));
  await chk('Anónimo no lee incidentes', assertFails(anonimo.collection('incidentes').get()));
  await chk('Cuadrilla resuelve un incidente', assertSucceeds(chofer.doc('incidentes/i1').update({ estado: 'resuelto' })));
  await chk('Cuadrilla no cambia el tipo de un incidente', assertFails(chofer.doc('incidentes/i1').update({ tipo: 'Otro' })));
  await chk('Cuadrilla no borra incidentes', assertFails(chofer.doc('incidentes/i1').delete()));
  await chk('Vecino no se declara autoridad en su dispositivo', assertFails(vecino.doc('dispositivos/tok2').set({ uid: 'u3', rol: 'autoridad', actualizado: new Date() })));
  await chk('Nadie toma el dispositivo de otra persona', assertFails(chofer.doc('dispositivos/tok-vecino').set({ uid: 'u2', rol: 'recolector', actualizado: new Date() })));
  await chk('Cuadrilla registra el vaciado de un contenedor', assertSucceeds(chofer.doc('telemetria_contenedores/ECO-SF-001').update({ porcentajeLlenado: 10, alertaDesborde: false, ultimaActualizacion: new Date() })));
  await chk('Cuadrilla no sube el llenado de un contenedor', assertFails(chofer.doc('telemetria_contenedores/ECO-SF-001').update({ porcentajeLlenado: 90 })));
  await chk('Vecino no registra vaciados', assertFails(vecino.doc('telemetria_contenedores/ECO-SF-001').update({ porcentajeLlenado: 10 })));
  console.log(`\n${ok}/${total} verificaciones OK`);
  await env.cleanup();
  process.exit(ok === total ? 0 : 1);
})();
