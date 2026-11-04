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
  console.log(`\n${ok}/${total} verificaciones OK`);
  await env.cleanup();
  process.exit(ok === total ? 0 : 1);
})();
