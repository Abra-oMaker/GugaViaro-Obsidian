import { QuartzComponent, QuartzComponentProps } from "./types"

const Translate: QuartzComponent = (_props: QuartzComponentProps) => {
  return (
    <div id="google-translate-container" style={{
      padding: "0.5rem 0",
      fontSize: "0.85rem",
    }}>
      <div id="google_translate_element"></div>
      <script
        dangerouslySetInnerHTML={{
          __html: `
            function googleTranslateElementInit() {
              new google.translate.TranslateElement(
                { pageLanguage: 'pt', layout: google.translate.TranslateElement.InlineLayout.SIMPLE },
                'google_translate_element'
              );
            }
          `,
        }}
      />
      <script src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit" />
    </div>
  )
}

Translate.displayName = "Translate"
export default Translate
