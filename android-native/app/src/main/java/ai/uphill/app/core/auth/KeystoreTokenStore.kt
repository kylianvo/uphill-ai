package ai.uphill.app.core.auth

import ai.uphill.app.core.networking.TokenStore
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.AtomicFile
import java.io.File
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class KeystoreTokenStore(directory: File) : TokenStore {
    private val file = AtomicFile(File(directory, "session.enc"))
    private val alias = "ai.uphill.app.session"

    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(alias, null) as? SecretKey)?.let {
            return it
        }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
            .apply {
                init(
                    KeyGenParameterSpec.Builder(
                            alias,
                            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
                        )
                        .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                        .build()
                )
            }
            .generateKey()
    }

    @Synchronized
    override fun read(): String? {
        if (!file.baseFile.exists()) return null
        return runCatching {
                val bytes = file.readFully()
                val cipher = Cipher.getInstance("AES/GCM/NoPadding")
                cipher.init(
                    Cipher.DECRYPT_MODE,
                    key(),
                    GCMParameterSpec(128, bytes.copyOfRange(0, 12)),
                )
                cipher.doFinal(bytes.copyOfRange(12, bytes.size)).toString(Charsets.UTF_8)
            }
            .getOrElse {
                file.delete()
                null
            }
    }

    @Synchronized
    override fun write(token: String?) {
        if (token == null) {
            file.delete()
            return
        }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val stream = file.startWrite()
        try {
            stream.write(cipher.iv + cipher.doFinal(token.toByteArray()))
            file.finishWrite(stream)
        } catch (e: Exception) {
            file.failWrite(stream)
            throw e
        }
    }
}
