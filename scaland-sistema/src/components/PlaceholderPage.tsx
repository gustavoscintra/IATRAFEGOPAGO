interface PlaceholderPageProps {
  title: string
  desc: string
  nextStep: string
}

export function PlaceholderPage({ title, desc, nextStep }: PlaceholderPageProps) {
  return (
    <>
      <div className="page-head">
        <div>
          <h1>{title}</h1>
          <div className="desc">{desc}</div>
        </div>
      </div>
      <div className="empty" style={{ border: '1px dashed var(--line-2)', borderRadius: 'var(--radius)' }}>
        <b>Esqueleto pronto, módulo vem a seguir</b>
        {nextStep}
      </div>
    </>
  )
}
