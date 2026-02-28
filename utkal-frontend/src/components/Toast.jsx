import React from "react";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";

const icons = {
    success: <CheckCircle className="w-5 h-5 text-success-content" />,
    error: <AlertCircle className="w-5 h-5 text-error-content" />,
    info: <Info className="w-5 h-5 text-info-content" />,
    warning: <AlertTriangle className="w-5 h-5 text-warning-content" />,
};

const alertClasses = {
    success: "alert-success",
    error: "alert-error",
    info: "alert-info",
    warning: "alert-warning",
};

export const ToastContainer = ({ toasts, remove }) => {
    return (
        <div className="toast toast-top toast-end z-[9999] p-4 flex flex-col gap-2">
            <AnimatePresence mode="popLayout">
                {toasts.map((toast) => (
                    <motion.div
                        key={toast.id}
                        layout
                        initial={{ opacity: 0, x: 50, scale: 0.9 }}
                        animate={{ opacity: 1, x: 0, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
                        className={clsx(
                            "alert shadow-2xl flex items-start gap-4 pr-10 min-w-[300px] border-none",
                            alertClasses[toast.type]
                        )}
                    >
                        <div className="flex-shrink-0 mt-0.5">
                            {icons[toast.type]}
                        </div>
                        <div className="flex-grow">
                            <p className="text-sm font-semibold">{toast.message}</p>
                        </div>
                        <button
                            className="absolute top-2 right-2 btn btn-ghost btn-xs btn-circle opacity-60 hover:opacity-100 transition-opacity"
                            onClick={() => remove(toast.id)}
                        >
                            <X className="w-3 h-3" />
                        </button>
                    </motion.div>
                ))}
            </AnimatePresence>
        </div>
    );
};
