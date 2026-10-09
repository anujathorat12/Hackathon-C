import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import Icon from './Icon'

const LOCAL_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '[::1]']

// "Try it yourself": a QR code for the address this studio is served from, for judges to scan.
export default function ShareButton() {
  const [open, setOpen] = useState(false)
  const [qr, setQr] = useState(null)
  const [copied, setCopied] = useState(false)
  const url = window.location.origin
  const local = LOCAL_HOSTS.includes(window.location.hostname)

  useEffect(() => {
    if (!open || qr) return
    import('qrcode')
      .then((QRCode) => QRCode.toDataURL(url, { margin: 1, width: 260, color: { dark: '#0b1020', light: '#ffffff' } }))
      .then(setQr)
      .catch(() => setQr(null))
  }, [open, qr, url])

  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open])

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch { /* clipboard blocked; the URL is visible to copy by hand */ }
  }

  return (
    <>
      <button className="btn btn-ghost share-btn" onClick={() => setOpen(true)}>
        <Icon name="upload" size={15} /> Share
      </button>
      {/* Portal to <body>: the header's backdrop-filter would otherwise trap this fixed overlay inside it. */}
      {open && createPortal(
        <div className="modal-scrim" onMouseDown={(e) => e.target === e.currentTarget && setOpen(false)}>
          <div className="modal share-modal" role="dialog" aria-modal="true" aria-labelledby="share-title">
            <div className="modal-head">
              <div>
                <span className="eyebrow"><Icon name="spark" size={14} /> Try it yourself</span>
                <h2 id="share-title">Scan to open ContentGenie</h2>
              </div>
              <button className="icon-btn" onClick={() => setOpen(false)} aria-label="Close"><Icon name="x" /></button>
            </div>
            <div className="share-body">
              <div className="share-qr">{qr ? <img src={qr} alt={`QR code for ${url}`} /> : <span className="spinner" />}</div>
              <div className="share-url">
                <code>{url}</code>
                <button className="btn btn-primary" onClick={copy}><Icon name={copied ? 'check' : 'file'} size={15} /> {copied ? 'Copied' : 'Copy link'}</button>
              </div>
              {local && (
                <div className="banner banner-warn small">
                  <Icon name="alert" size={16} /> This address only works on this computer. Deploy the app (see README → “Public link”) to get a link anyone can open.
                </div>
              )}
            </div>
          </div>
        </div>,
        document.body,
      )}
    </>
  )
}
