import '../index.css';

interface Props {
    handle: () => void;
    text: string;
    textColor: string; 
    iSdisabled ?: boolean;
    IncMinWidth?:string;
  }
  
  export default function Button({ handle, text, textColor, iSdisabled,IncMinWidth }: Props) {

    return (
      <button
        type="button"
        onClick={handle}
        style={{
          color: iSdisabled ? 'rgba(255, 255, 255, 0.5)' : `var(${textColor})`, 
          minWidth: `${IncMinWidth}`
        }}
        className={`bg-black px-6 py-3 rounded-full 
                    hover:bg-transparent hover:text-black transition-colors
                    inter-500 text-xs border border-black tracking-wider ${IncMinWidth==="118px" && `min-w-[${IncMinWidth}]`}
                    disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-black`}
        onMouseEnter={(e) => {
          if (!iSdisabled) {
            e.currentTarget.style.color = "black";
            e.currentTarget.style.backgroundColor = "transparent";
          }
        }}
        onMouseLeave={(e) => {
          if (!iSdisabled) {
            e.currentTarget.style.color = `var(${textColor})`;
            e.currentTarget.style.backgroundColor = "black";
          }
        }}
        disabled={iSdisabled}
        
      >
        {text}
      </button>
    );
  }
  