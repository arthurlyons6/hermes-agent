/**
 * `hermes:fs:reveal` answers what it did (#115167). `shell.showItemInFolder`
 * selects an existing item and silently no-ops on a missing one, and a remote
 * backend's paths are missing on this computer by construction — a `true` for
 * them left the renderer nothing to say.
 */
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import { afterEach, describe, expect, it, vi } from 'vitest'

const electron = vi.hoisted(() => ({
  handlers: new Map<string, (...args: unknown[]) => unknown>(),
  showItemInFolder: vi.fn()
}))

vi.mock('electron', () => ({
  ipcMain: {
    handle: (channel: string, handler: (...args: unknown[]) => unknown) => electron.handlers.set(channel, handler)
  },
  shell: {
    showItemInFolder: electron.showItemInFolder,
    openPath: vi.fn(async () => '')
  }
}))

vi.mock('./desktop-plugin-install', () => ({ installDesktopPluginFromGit: vi.fn(), probePluginRepo: vi.fn() }))
vi.mock('./desktop-plugins-root', () => ({
  DESKTOP_PLUGINS_DIR: 'desktop-plugins',
  ensureDir: vi.fn(async (dir: string) => dir),
  migrateProfileScopedDesktopPlugins: vi.fn(),
  reconcileUnifiedDesktopHalves: vi.fn()
}))

import { registerFsIpc } from './fs-ipc'

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'hermes-fs-ipc-'))

registerFsIpc({
  hermesHome: scratch,
  readActiveDesktopProfile: () => 'launch-profile',
  // `~/` resolves under the scratch dir so tilde paths can be exercised.
  expandUserPath: value => (value.startsWith('~/') ? path.join(scratch, value.slice(2)) : value),
  resolveRequestedPathForIpc: value => value,
  directoryExists: value => fs.existsSync(value),
  resolveGitBinary: () => 'git'
})

// R-4 sender-trust hardening: every handler asserts the message came from the
// app's own main frame (`senderFrame === sender.mainFrame`). A bare `{}` event
// is untrusted by construction, so the harness builds a trusted one.
const trustedEvent = () => {
  const mainFrame = { url: 'hermes://app/index.html' }

  return { senderFrame: mainFrame, sender: { mainFrame } }
}

const reveal = (target: string) => electron.handlers.get('hermes:fs:reveal')!(trustedEvent(), target)

afterEach(() => {
  electron.showItemInFolder.mockClear()
})

describe('hermes:fs:reveal', () => {
  it('reveals a path that exists on this computer', async () => {
    const file = path.join(scratch, 'workspace')
    fs.mkdirSync(file)

    await expect(reveal(file)).resolves.toBe(true)
    expect(electron.showItemInFolder).toHaveBeenCalledWith(file)
  })

  // A remote backend's workspace is not on this machine: showItemInFolder
  // would silently no-op, so the door must report the miss instead of success.
  it('reports false without touching the file manager when the path is missing', async () => {
    await expect(reveal(path.join(scratch, 'not-here'))).resolves.toBe(false)
    expect(electron.showItemInFolder).not.toHaveBeenCalled()
  })

  // The renderer may hand over a tilde path; the existence check runs on the
  // expanded path, and the expanded path is what the file manager is shown.
  it('expands a tilde path before checking and revealing it', async () => {
    const here = path.join(scratch, 'tilde.md')

    fs.writeFileSync(here, 'x')

    await expect(reveal('~/tilde.md')).resolves.toBe(true)
    expect(electron.showItemInFolder).toHaveBeenCalledWith(here)
  })
})

// A pooled backend serves several profile homes; the active Desktop profile
// is the LAUNCH one, so the error card names the profile owning the failing
// session and the root resolves under THAT home (#119080).
describe('hermes:fs:logsRoot', () => {
  const logsRoot = (profile?: string) => electron.handlers.get('hermes:fs:logsRoot')!(trustedEvent(), profile)

  it('resolves the logs dir of the profile that owns the session', async () => {
    await expect(logsRoot('finex')).resolves.toBe(path.join(scratch, 'profiles', 'finex', 'logs'))
    await expect(logsRoot('default')).resolves.toBe(path.join(scratch, 'logs'))
  })

  it('falls back to the active Desktop profile when no owner is named', async () => {
    await expect(logsRoot()).resolves.toBe(path.join(scratch, 'profiles', 'launch-profile', 'logs'))
  })

  // The owner is renderer data (from a remote backend in remote mode): a
  // traversal or absolute value must never leave hermesHome, let alone be
  // created and revealed. Bad names route like an unnamed owner.
  it('never leaves hermesHome for an owner that is not a profile name', async () => {
    for (const bad of ['../../x', '/etc', 'a/b', 'Upper', '.hidden']) {
      const root = (await logsRoot(bad)) as string

      expect(path.relative(scratch, root).startsWith('..')).toBe(false)
      expect(root).toBe(path.join(scratch, 'profiles', 'launch-profile', 'logs'))
    }
  })
})

// SF-7: the read chain blocked sensitive files; the write chain did not, so a
// compromised trusted renderer could overwrite .env / .ssh / .aws credentials
// through `hermes:fs:writeText`. The block is now applied to the write too.
describe('hermes:fs:writeText sensitive-file block (SF-7)', () => {
  const writeText = (filePath: string, content: string) =>
    electron.handlers.get('hermes:fs:writeText')!(trustedEvent(), filePath, content)

  it('writes an ordinary text file', async () => {
    const target = path.join(scratch, 'ordinary.md')

    await expect(writeText(target, 'hello')).resolves.toEqual({ path: target })
    expect(fs.readFileSync(target, 'utf8')).toBe('hello')
  })

  // The block fires on the resolved path, before the parent-exists check, so
  // the error names the block — not a missing directory — and nothing is
  // written even when the parent does exist.
  it('refuses to overwrite a credential file', async () => {
    const env = path.join(scratch, '.env')

    fs.writeFileSync(env, 'SECRET=keep-me')

    await expect(writeText(env, 'SECRET=clobbered')).rejects.toThrow(/sensitive file/)
    expect(fs.readFileSync(env, 'utf8')).toBe('SECRET=keep-me')
  })

  // A tilde path is expanded before the check, so `~/.ssh/id_rsa` from the
  // renderer is blocked the same as an absolute path.
  it('blocks a tilde-expanded credential path', async () => {
    await expect(writeText('~/.ssh/id_rsa', 'PRIVATE KEY')).rejects.toThrow(/sensitive file/)
    expect(fs.existsSync(path.join(scratch, '.ssh', 'id_rsa'))).toBe(false)
  })

  // The blocklist's other shapes: .aws/credentials needs its directory
  // component, .npmrc and .pem match by basename/extension, and .env.<suffix>
  // is blocked unless the suffix is a known-safe template name.
  it('blocks every credential shape the read chain blocks', async () => {
    const cases: Array<[string, string]> = [
      [path.join('.aws', 'credentials'), '.aws/credentials'],
      ['.npmrc', '.npmrc'],
      ['client.pem', 'client.pem'],
      ['.env.production', '.env.production'],
      ['id_ed25519', 'id_ed25519']
    ]

    for (const [relative, label] of cases) {
      const target = path.join(scratch, relative)

      await expect(writeText(target, 'x'), label).rejects.toThrow(/sensitive file/)
      expect(fs.existsSync(target), label).toBe(false)
    }
  })

  // A public key is NOT credential material — but note the .ssh DIRECTORY
  // rule fires first, so the exception only holds outside credential dirs.
  it('allows an ssh public key outside credential directories', async () => {
    const target = path.join(scratch, 'id_ed25519.pub')

    await expect(writeText(target, 'ssh-ed25519 AAAA')).resolves.toEqual({ path: target })
    expect(fs.readFileSync(target, 'utf8')).toBe('ssh-ed25519 AAAA')
  })

  // .env.example is a safe template name (SAFE_ENV_SUFFIXES) — blocking it
  // would break committing example env files.
  it('allows a safe .env template through', async () => {
    const target = path.join(scratch, '.env.example')

    await expect(writeText(target, 'SECRET=')).resolves.toEqual({ path: target })
  })
})
